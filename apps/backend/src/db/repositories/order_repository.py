"""
Uzinex Boost — Order Repository
===============================

Репозиторий для работы с заказами пользователей (ORM-модель Order).

Назначение:
- создание и управление заказами на продвижение;
- изменение статусов (active, paused, completed);
- обновление бюджета и статистики выполнения;
- выборка активных заказов и аналитики.

Используется в:
- domain.services.orders
- api.v1.routes.orders
- adapters.payments
"""

from __future__ import annotations
from typing import List, Optional
from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.order_model import Order, OrderStatus
from db.repositories.base import BaseRepository


class OrderRepository(BaseRepository[Order]):
    """
    Репозиторий заказов — расширяет базовые CRUD-функции.
    """

    def __init__(self, session: AsyncSession):
        super().__init__(session, Order)

    # -------------------------------------------------
    # 🔹 Получить все активные заказы
    # -------------------------------------------------
    async def get_active_orders(self, limit: int = 100) -> List[Order]:
        """
        Возвращает список всех активных заказов.
        """
        result = await self.session.execute(
            select(Order).where(Order.status == OrderStatus.ACTIVE).limit(limit)
        )
        return result.scalars().all()

    # -------------------------------------------------
    # 🔹 Получить заказы конкретного пользователя
    # -------------------------------------------------
    async def get_by_user(self, user_id: int, include_completed: bool = False) -> List[Order]:
        """
        Возвращает все заказы пользователя.
        """
        query = select(Order).where(Order.user_id == user_id)
        if not include_completed:
            query = query.where(Order.status != OrderStatus.COMPLETED)
        result = await self.session.execute(query.order_by(Order.created_at.desc()))
        return result.scalars().all()

    # -------------------------------------------------
    # 🔹 Обновить статус заказа
    # -------------------------------------------------
    async def update_status(self, order_id: int, status: OrderStatus) -> Optional[Order]:
        """
        Изменяет статус заказа (active, paused, completed, canceled).
        """
        await self.session.execute(
            update(Order)
            .where(Order.id == order_id)
            .values(status=status)
            .execution_options(synchronize_session="fetch")
        )
        await self.session.commit()
        return await self.get(order_id)

    # -------------------------------------------------
    # 🔹 Списать средства из бюджета
    # -------------------------------------------------
    async def spend_budget(self, order_id: int, amount: float) -> Optional[Order]:
        """
        Уменьшает доступный бюджет заказа после выполненного задания.
        """
        result = await self.session.execute(select(Order).where(Order.id == order_id))
        order = result.scalar_one_or_none()
        if not order:
            return None

        order.spent += amount
        order.actions_completed += 1
        if order.spent >= order.total_budget:
            order.status = OrderStatus.COMPLETED

        await self.session.commit()
        await self.session.refresh(order)
        return order

    # -------------------------------------------------
    # 🔹 Подсчёт заказов по статусам
    # -------------------------------------------------
    async def count_by_status(self, user_id: Optional[int] = None) -> dict:
        """
        Возвращает статистику количества заказов по статусам.
        """
        query = select(Order.status, func.count(Order.id)).group_by(Order.status)
        if user_id:
            query = query.where(Order.user_id == user_id)
        result = await self.session.execute(query)
        return {status.value: count for status, count in result.all()}
