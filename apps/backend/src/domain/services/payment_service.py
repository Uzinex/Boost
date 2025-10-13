"""
Uzinex Boost — Payment Service
==============================

Сервис управления платежами и финансовыми операциями.

Назначение:
-----------
Реализует взаимодействие с платёжными системами:
- приём депозитов (ввод средств);
- вывод средств;
- возвраты и отмены;
- обновление статусов и синхронизация с балансом;
- аналитика и история платежей.

Используется в:
- domain.services.balance_service
- domain.rules.payment_rules
- domain.events.payment_events
- api.v1.routes.payment
"""

from __future__ import annotations
from typing import Optional
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from domain.services.base import BaseService
from domain.services.balance_service import BalanceService
from domain.rules.payment_rules import PaymentRules
from domain.events.payment_events import (
    PaymentCreatedEvent,
    PaymentCompletedEvent,
    PaymentFailedEvent,
    PaymentRefundedEvent,
)
from db.repositories.payment_repository import PaymentRepository
from db.repositories.transaction_repository import TransactionRepository


class PaymentService(BaseService):
    """
    Управляет всеми платёжными процессами (депозиты, выводы, возвраты).
    """

    def __init__(self, session: AsyncSession):
        super().__init__(session)
        self.payment_repo = PaymentRepository(session)
        self.tx_repo = TransactionRepository(session)
        self.balance_service = BalanceService(session)

    # -------------------------------------------------
    # 🔹 Создание нового платежа
    # -------------------------------------------------
    async def create_payment(
        self,
        user_id: int,
        amount: float,
        method: str,
        direction: str,  # 'in' (deposit) или 'out' (withdraw)
        metadata: Optional[dict] = None,
    ):
        """
        Создаёт запись о новом платеже (ожидание подтверждения).
        """
        # Проверяем метод оплаты по правилам
        rule = await PaymentRules.validate_method(user_id=user_id, method=method)
        if not rule.is_allowed:
            return {"success": False, "message": rule.message}

        payment = await self.payment_repo.create_payment(
            user_id=user_id,
            amount=amount,
            method=method,
            direction=direction,
            status="pending",
            metadata=metadata or {},
        )

        await self.publish_event(
            PaymentCreatedEvent(
                payment_id=payment.id,
                user_id=user_id,
                amount=amount,
                method=method,
                direction=direction,
            )
        )
        await self.commit()
        await self.log(f"Создан платёж {payment.id} ({direction}, {amount} UZT, {method})")
        return {"success": True, "payment_id": payment.id, "status": payment.status}

    # -------------------------------------------------
    # 🔹 Подтверждение успешного платежа
    # -------------------------------------------------
    async def complete_payment(self, payment_id: int):
        """
        Подтверждает успешное выполнение платежа.
        """
        payment = await self.payment_repo.get_by_id(payment_id)
        if not payment:
            return {"success": False, "message": "Платёж не найден"}

        if payment.status == "completed":
            return {"success": False, "message": "Платёж уже подтверждён"}

        payment.status = "completed"
        payment.completed_at = datetime.utcnow()

        # Синхронизация с балансом
        if payment.direction == "in":
            await self.balance_service.deposit(
                user_id=payment.user_id,
                amount=payment.amount,
                payment_id=payment.id,
            )
        elif payment.direction == "out":
            await self.balance_service.withdraw(
                user_id=payment.user_id,
                amount=payment.amount,
            )

        await self.publish_event(
            PaymentCompletedEvent(
                payment_id=payment.id,
                user_id=payment.user_id,
                amount=payment.amount,
                method=payment.method,
                direction=payment.direction,
            )
        )
        await self.commit()
        await self.log(f"Платёж подтверждён: {payment.id}")
        return {"success": True, "status": "completed"}

    # -------------------------------------------------
    # 🔹 Отметить платёж как неудавшийся
    # -------------------------------------------------
    async def fail_payment(self, payment_id: int, reason: Optional[str] = None):
        """
        Помечает платёж как неуспешный.
        """
        payment = await self.payment_repo.get_by_id(payment_id)
        if not payment:
            return {"success": False, "message": "Платёж не найден"}

        payment.status = "failed"
        payment.failed_reason = reason or "Неизвестная ошибка"
        payment.failed_at = datetime.utcnow()

        await self.publish_event(
            PaymentFailedEvent(
                payment_id=payment.id,
                user_id=payment.user_id,
                amount=payment.amount,
                reason=payment.failed_reason,
            )
        )
        await self.commit()
        await self.log(f"Платёж неуспешен: {payment.id} ({reason})")
        return {"success": True, "status": "failed"}

    # -------------------------------------------------
    # 🔹 Возврат платежа
    # -------------------------------------------------
    async def refund_payment(self, payment_id: int, reason: Optional[str] = None):
        """
        Возвращает средства пользователю (рефанд).
        """
        payment = await self.payment_repo.get_by_id(payment_id)
        if not payment or payment.status != "completed":
            return {"success": False, "message": "Платёж не найден или не завершён"}

        # Проверка правила возврата
        rule = await PaymentRules.can_refund(payment)
        if not rule.is_allowed:
            return {"success": False, "message": rule.message}

        payment.status = "refunded"
        payment.refunded_at = datetime.utcnow()

        # Возврат на баланс
        await self.balance_service.deposit(
            user_id=payment.user_id,
            amount=payment.amount,
            payment_id=payment.id,
        )

        await self.publish_event(
            PaymentRefundedEvent(
                payment_id=payment.id,
                user_id=payment.user_id,
                amount=payment.amount,
                reason=reason or "Возврат средств",
            )
        )
        await self.commit()
        await self.log(f"Платёж возвращён: {payment.id} (+{payment.amount} UZT)")
        return {"success": True, "status": "refunded"}

    # -------------------------------------------------
    # 🔹 Получить историю платежей
    # -------------------------------------------------
    async def get_payment_history(self, user_id: int, limit: int = 50):
        """
        Возвращает историю платежей пользователя.
        """
        payments = await self.payment_repo.get_by_user(user_id, limit)
        return [p.as_dict() for p in payments]

    # -------------------------------------------------
    # 🔹 Глобальная статистика
    # -------------------------------------------------
    async def get_global_stats(self):
        """
        Возвращает агрегированные данные по всем платежам.
        """
        stats = await self.payment_repo.get_stats()
        await self.log("Получена глобальная статистика платежей")
        return stats
