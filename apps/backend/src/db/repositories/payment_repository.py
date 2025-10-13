"""
Uzinex Boost — Payment Repository
==================================

Репозиторий для работы с платежами пользователей (ORM-модель Payment).

Назначение:
- хранение и управление пополнениями баланса (UZT);
- проверка, фильтрация и подтверждение чеков;
- интеграция с админ-панелью и платёжными системами (Click, Payme, Manual).

Используется в:
- domain.services.payments
- api.v1.routes.payments
- adapters.payments.manual
"""

from __future__ import annotations
from typing import List, Optional
from datetime import datetime

from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.payment_model import Payment, PaymentStatus, PaymentMethod
from db.repositories.base import BaseRepository


class PaymentRepository(BaseRepository[Payment]):
    """
    Репозиторий для управления платежами пользователей.
    """

    def __init__(self, session: AsyncSession):
        super().__init__(session, Payment)

    # -------------------------------------------------
    # 🔹 Получить все платежи пользователя
    # -------------------------------------------------
    async def get_by_user(self, user_id: int, include_rejected: bool = False) -> List[Payment]:
        """
        Возвращает список всех платежей пользователя.
        """
        query = select(Payment).where(Payment.user_id == user_id)
        if not include_rejected:
            query = query.where(Payment.status != PaymentStatus.REJECTED)
        result = await self.session.execute(query.order_by(Payment.created_at.desc()))
        return result.scalars().all()

    # -------------------------------------------------
    # 🔹 Получить все ожидающие подтверждения платежи
    # -------------------------------------------------
    async def get_pending(self, limit: int = 100) -> List[Payment]:
        """
        Возвращает список ожидающих подтверждения платежей (для админов).
        """
        result = await self.session.execute(
            select(Payment)
            .where(Payment.status == PaymentStatus.PENDING)
            .order_by(Payment.created_at.asc())
            .limit(limit)
        )
        return result.scalars().all()

    # -------------------------------------------------
    # 🔹 Подтвердить платёж
    # -------------------------------------------------
    async def verify_payment(self, payment_id: int, admin_id: int) -> Optional[Payment]:
        """
        Подтверждает платёж (меняет статус на VERIFIED и фиксирует администратора).
        """
        await self.session.execute(
            update(Payment)
            .where(Payment.id == payment_id)
            .values(
                status=PaymentStatus.VERIFIED,
                verified_by=admin_id,
                verified_at=datetime.utcnow(),
            )
            .execution_options(synchronize_session="fetch")
        )
        await self.session.commit()
        return await self.get(payment_id)

    # -------------------------------------------------
    # 🔹 Отклонить платёж
    # -------------------------------------------------
    async def reject_payment(self, payment_id: int, admin_id: int, comment: str = "") -> Optional[Payment]:
        """
        Отклоняет платёж (меняет статус на REJECTED и добавляет комментарий).
        """
        await self.session.execute(
            update(Payment)
            .where(Payment.id == payment_id)
            .values(
                status=PaymentStatus.REJECTED,
                verified_by=admin_id,
                verified_at=datetime.utcnow(),
                comment=comment,
            )
            .execution_options(synchronize_session="fetch")
        )
        await self.session.commit()
        return await self.get(payment_id)

    # -------------------------------------------------
    # 🔹 Статистика по платежам
    # -------------------------------------------------
    async def get_stats(self, user_id: Optional[int] = None) -> dict:
        """
        Возвращает агрегированную статистику по платежам:
        общее количество, общая сумма, успешные, отклонённые, ожидающие.
        """
        query = select(
            Payment.status,
            func.count(Payment.id),
            func.sum(Payment.amount),
        ).group_by(Payment.status)

        if user_id:
            query = query.where(Payment.user_id == user_id)

        result = await self.session.execute(query)
        stats = {}
        for status, count, total in result.all():
            stats[status.value] = {"count": count, "sum": float(total or 0)}

        # Добавим общие суммы
        stats["total"] = {
            "count": sum(v["count"] for v in stats.values()),
            "sum": round(sum(v["sum"] for v in stats.values()), 2),
        }

        return stats

    # -------------------------------------------------
    # 🔹 Получить последние N платежей
    # -------------------------------------------------
    async def get_recent(self, limit: int = 10) -> List[Payment]:
        """
        Возвращает последние платежи (для дашборда админа).
        """
        result = await self.session.execute(
            select(Payment).order_by(Payment.created_at.desc()).limit(limit)
        )
        return result.scalars().all()
