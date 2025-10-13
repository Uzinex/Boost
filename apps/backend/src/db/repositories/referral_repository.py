"""
Uzinex Boost — Referral Repository
==================================

Репозиторий для работы с реферальными связями пользователей.

Назначение:
- управление связями "пригласил → приглашённый";
- начисление бонусов за приглашения;
- статистика по количеству и сумме бонусов;
- поддержка аналитики роста платформы.

Используется в:
- domain.services.referrals
- api.v1.routes.users
- balance/transaction logic
"""

from __future__ import annotations
from typing import List, Optional
from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.referral_model import Referral
from db.repositories.base import BaseRepository


class ReferralRepository(BaseRepository[Referral]):
    """
    Репозиторий для управления реферальными связями.
    """

    def __init__(self, session: AsyncSession):
        super().__init__(session, Referral)

    # -------------------------------------------------
    # 🔹 Получить всех приглашённых пользователем
    # -------------------------------------------------
    async def get_referrals_by_user(self, referrer_id: int) -> List[Referral]:
        """
        Возвращает всех пользователей, приглашённых данным пользователем.
        """
        result = await self.session.execute(
            select(Referral)
            .where(Referral.referrer_id == referrer_id)
            .order_by(Referral.joined_at.desc())
        )
        return result.scalars().all()

    # -------------------------------------------------
    # 🔹 Проверить, есть ли реферальная связь
    # -------------------------------------------------
    async def get_by_referred(self, referred_id: int) -> Optional[Referral]:
        """
        Проверяет, зарегистрирован ли пользователь как реферал.
        """
        result = await self.session.execute(
            select(Referral).where(Referral.referred_id == referred_id)
        )
        return result.scalar_one_or_none()

    # -------------------------------------------------
    # 🔹 Начислить бонус
    # -------------------------------------------------
    async def add_bonus(self, referred_id: int, amount: float) -> Optional[Referral]:
        """
        Добавляет бонус рефералу (увеличивает bonus_amount).
        """
        await self.session.execute(
            update(Referral)
            .where(Referral.referred_id == referred_id)
            .values(bonus_amount=Referral.bonus_amount + amount)
            .execution_options(synchronize_session="fetch")
        )
        await self.session.commit()
        return await self.get_by_referred(referred_id)

    # -------------------------------------------------
    # 🔹 Статистика по рефералам пользователя
    # -------------------------------------------------
    async def get_referral_stats(self, referrer_id: int) -> dict:
        """
        Возвращает статистику реферальной программы:
        - общее количество приглашённых;
        - сумма бонусов за них.
        """
        result = await self.session.execute(
            select(
                func.count(Referral.id),
                func.sum(Referral.bonus_amount),
            ).where(Referral.referrer_id == referrer_id)
        )
        total_referrals, total_bonus = result.first() or (0, 0.0)
        return {
            "total_referrals": total_referrals or 0,
            "total_bonus": round(float(total_bonus or 0), 2),
        }

    # -------------------------------------------------
    # 🔹 Глобальная статистика по всем пользователям
    # -------------------------------------------------
    async def get_global_stats(self) -> dict:
        """
        Возвращает общие метрики по всем реферальным связям:
        - общее количество связей;
        - общее количество бонусов;
        - средний бонус.
        """
        result = await self.session.execute(
            select(
                func.count(Referral.id),
                func.sum(Referral.bonus_amount),
                func.avg(Referral.bonus_amount),
            )
        )
        count, total_bonus, avg_bonus = result.first() or (0, 0.0, 0.0)
        return {
            "total_links": count or 0,
            "total_bonus": round(float(total_bonus or 0), 2),
            "avg_bonus": round(float(avg_bonus or 0), 2),
        }
    