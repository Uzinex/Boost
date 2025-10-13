"""
Uzinex Boost — Order Service
============================

Сервис для управления заказами (orders) в системе Uzinex Boost.

Назначение:
-----------
Реализует все бизнес-операции с заказами:
- создание и публикация;
- принятие исполнителем;
- выполнение, завершение и отмена;
- расчёт комиссий и синхронизация баланса.

Используется в:
- api.v1.routes.order
- domain.rules.order_rules
- domain.events.order_events
- db.repositories.order_repository
- domain.services.payment_service
"""

from __future__ import annotations
from typing import Optional
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from domain.services.base import BaseService
from domain.rules.order_rules import OrderRules
from domain.events.order_events import (
    OrderCreatedEvent,
    OrderAcceptedEvent,
    OrderCompletedEvent,
    OrderCancelledEvent,
)
from domain.services.balance_service import BalanceService
from db.repositories.order_repository import OrderRepository
from db.repositories.user_repository import UserRepository


class OrderService(BaseService):
    """
    Управляет заказами: создание, принятие, выполнение, отмена.
    """

    def __init__(self, session: AsyncSession):
        super().__init__(session)
        self.order_repo = OrderRepository(session)
        self.user_repo = UserRepository(session)
        self.balance_service = BalanceService(session)

    # -------------------------------------------------
    # 🔹 Создание нового заказа
    # -------------------------------------------------
    async def create_order(
        self,
        client_id: int,
        title: str,
        description: str,
        price: float,
        deadline: Optional[datetime] = None,
    ):
        """
        Создаёт заказ от клиента.
        Проверяет правила, баланс и публикует событие.
        """
        client = await self.user_repo.get_by_id(client_id)
        if not client:
            return {"success": False, "message": "Клиент не найден"}

        active_orders = await self.order_repo.count_active_by_client(client_id)
        rule = await OrderRules.can_create_order(client, price, active_orders)
        if not rule.is_allowed:
            return {"success": False, "message": rule.message}

        # Проверка баланса
        balance = await self.balance_service.get_balance(client_id)
        if balance is None or balance < price:
            return {"success": False, "message": "Недостаточно средств на балансе"}

        # Списываем средства под эскроу
        await self.balance_service.withdraw(client_id, price)

        # Создаём заказ
        order = await self.order_repo.create_order(
            client_id=client_id,
            title=title,
            description=description,
            price=price,
            deadline=deadline or datetime.utcnow() + timedelta(days=7),
        )

        await self.publish_event(
            OrderCreatedEvent(order_id=order.id, client_id=client_id, price=price)
        )
        await self.commit()
        await self.log(f"Создан заказ {order.id} клиентом {client_id}")
        return {"success": True, "order_id": order.id}

    # -------------------------------------------------
    # 🔹 Принятие заказа исполнителем
    # -------------------------------------------------
    async def accept_order(self, performer_id: int, order_id: int):
        """
        Исполнитель принимает заказ в работу.
        """
        performer = await self.user_repo.get_by_id(performer_id)
        order = await self.order_repo.get_by_id(order_id)
        if not performer or not order:
            return {"success": False, "message": "Исполнитель или заказ не найден"}

        if order.status != "open":
            return {"success": False, "message": "Заказ уже в работе или завершён"}

        active_orders = await self.order_repo.count_active_by_performer(performer_id)
        rule = await OrderRules.can_accept_order(performer, active_orders)
        if not rule.is_allowed:
            return {"success": False, "message": rule.message}

        order.performer_id = performer_id
        order.status = "in_progress"
        order.accepted_at = datetime.utcnow()

        await self.publish_event(
            OrderAcceptedEvent(order_id=order.id, performer_id=performer_id)
        )
        await self.commit()
        await self.log(f"Исполнитель {performer_id} принял заказ {order_id}")
        return {"success": True, "status": "in_progress"}

    # -------------------------------------------------
    # 🔹 Завершение заказа
    # -------------------------------------------------
    async def complete_order(self, order_id: int):
        """
        Завершает заказ после выполнения и проверки.
        """
        order = await self.order_repo.get_by_id(order_id)
        if not order:
            return {"success": False, "message": "Заказ не найден"}

        rule = await OrderRules.can_complete_order(order.status, order.deadline)
        if not rule.is_allowed:
            return {"success": False, "message": rule.message}

        order.status = "completed"
        order.completed_at = datetime.utcnow()

        # Расчёт комиссии и выплата исполнителю
        fee_data = await OrderRules.calculate_fee(order.price)
        net = fee_data["net_amount"]
        performer_id = order.performer_id

        if performer_id:
            await self.balance_service.deposit(performer_id, net)

        await self.publish_event(
            OrderCompletedEvent(
                order_id=order.id,
                performer_id=performer_id,
                price=order.price,
                net_amount=net,
                platform_fee=fee_data["fee"],
            )
        )
        await self.commit()
        await self.log(f"Заказ {order_id} завершён, выплачено {net} UZT")
        return {"success": True, "status": "completed"}

    # -------------------------------------------------
    # 🔹 Отмена заказа
    # -------------------------------------------------
    async def cancel_order(self, order_id: int, user_id: int, user_role: str):
        """
        Отмена заказа (по инициативе клиента или администратора).
        """
        order = await self.order_repo.get_by_id(order_id)
        if not order:
            return {"success": False, "message": "Заказ не найден"}

        rule = await OrderRules.can_cancel_order(order.status, user_role)
        if not rule.is_allowed:
            return {"success": False, "message": rule.message}

        order.status = "cancelled"
        order.cancelled_at = datetime.utcnow()

        # Возврат средств клиенту, если заказ не начался
        if order.status == "open":
            await self.balance_service.deposit(order.client_id, order.price)

        await self.publish_event(
            OrderCancelledEvent(order_id=order.id, user_id=user_id, role=user_role)
        )
        await self.commit()
        await self.log(f"Заказ {order_id} отменён пользователем {user_id}")
        return {"success": True, "status": "cancelled"}

    # -------------------------------------------------
    # 🔹 Получение списка заказов
    # -------------------------------------------------
    async def get_user_orders(self, user_id: int, role: str, limit: int = 50):
        """
        Возвращает заказы клиента или исполнителя.
        """
        if role == "client":
            orders = await self.order_repo.get_by_client(user_id, limit)
        else:
            orders = await self.order_repo.get_by_performer(user_id, limit)
        return [o.as_dict() for o in orders]

    # -------------------------------------------------
    # 🔹 Глобальная статистика по заказам
    # -------------------------------------------------
    async def get_global_stats(self):
        """
        Возвращает общую статистику по заказам.
        """
        stats = await self.order_repo.get_stats()
        await self.log("Получена глобальная статистика заказов")
        return stats
