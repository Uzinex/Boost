"""
Uzinex Boost — Referral Service
===============================

Сервис для управления реферальной системой и бонусами.

Назначение:
-----------
Реализует бизнес-логику партнёрской программы:
- учёт приглашений;
- начисление бонусов;
- проверка лимитов и активности;
- повышение уровня участников;
- антифрод и лимиты по времени.

Используется в:
- api.v1.routes.referral
- domain.rules.referral_rules
- domain.events.referral_events
- db.repositories.referral_repository
- domain.services.balance_service
"""

from __future__ import annotations
from datetime import datetime
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from domain.services.base import BaseService
from domain.rules.referral_rules import ReferralRules
from domain.events.referral_events import (
    ReferralRegisteredEvent,
    ReferralBonusGrantedEvent,
    ReferralLevelUpEvent,
)
from domain.services.balance_service import BalanceService
from db.repositories.referral_repository import ReferralRepository
from db.repositories.user_repository import UserRepository


class ReferralService(BaseService):
    """
    Управляет логикой реферальной программы Uzinex Boost.
    """

    def __init__(self, session: AsyncSession):
        super().__init__(session)
        self.ref_repo = ReferralRepository(session)
        self.user_repo = UserRepository(session)
        self.balance_service = BalanceService(session)

    # -------------------------------------------------
    # 🔹 Добавить нового реферала
    # -------------------------------------------------
    async def register_referral(self, inviter_id: int, referral_id: int):
        """
        Добавляет нового реферала (приглашённого пользователя).
        """
        total_referrals = await self.ref_repo.count_by_inviter(inviter_id)
        rule = await ReferralRules.can_invite(inviter_id, total_referrals)
        if not rule.is_allowed:
            return {"success": False, "message": rule.message}

        record = await self.ref_repo.create_referral(
            inviter_id=inviter_id,
            referral_id=referral_id,
            joined_at=datetime.utcnow(),
        )

        await self.publish_event(
            ReferralRegisteredEvent(inviter_id=inviter_id, referral_id=referral_id)
        )
        await self.commit()
        await self.log(f"Новый реферал {referral_id} добавлен пользователем {inviter_id}")
        return {"success": True, "referral_id": record.referral_id}

    # -------------------------------------------------
    # 🔹 Начислить бонус за регистрацию
    # -------------------------------------------------
    async def grant_signup_bonus(self, inviter_id: int, referral_id: int, referral_joined_at: datetime):
        """
        Начисляет бонус за регистрацию приглашённого пользователя.
        """
        rule = await ReferralRules.can_receive_signup_bonus(referral_joined_at)
        if not rule.is_allowed:
            return {"success": False, "message": rule.message}

        # Проверка дневного лимита
        today_sum = await self.ref_repo.get_today_bonus_sum(inviter_id)
        limit_check = await ReferralRules.check_daily_bonus_limit(today_sum)
        if not limit_check.is_allowed:
            return {"success": False, "message": limit_check.message}

        await self.balance_service.deposit(inviter_id, amount=5000)

        await self.ref_repo.add_bonus_record(
            inviter_id=inviter_id,
            referral_id=referral_id,
            bonus_amount=5000,
            bonus_type="signup",
        )

        await self.publish_event(
            ReferralBonusGrantedEvent(
                inviter_id=inviter_id,
                referral_id=referral_id,
                amount=5000,
                bonus_type="signup",
            )
        )
        await self.commit()
        await self.log(f"Бонус за регистрацию начислен пользователю {inviter_id}")
        return {"success": True, "amount": 5000}

    # -------------------------------------------------
    # 🔹 Начислить бонус за активность реферала
    # -------------------------------------------------
    async def grant_task_bonus(self, inviter_id: int, referral_id: int, first_task_date: datetime):
        """
        Начисляет бонус за активность реферала (выполнил первое задание).
        """
        rule = await ReferralRules.can_receive_task_bonus(first_task_date)
        if not rule.is_allowed:
            return {"success": False, "message": rule.message}

        # Проверка лимитов
        today_sum = await self.ref_repo.get_today_bonus_sum(inviter_id)
        limit_check = await ReferralRules.check_daily_bonus_limit(today_sum)
        if not limit_check.is_allowed:
            return {"success": False, "message": limit_check.message}

        await self.balance_service.deposit(inviter_id, amount=3000)

        await self.ref_repo.add_bonus_record(
            inviter_id=inviter_id,
            referral_id=referral_id,
            bonus_amount=3000,
            bonus_type="task",
        )

        await self.publish_event(
            ReferralBonusGrantedEvent(
                inviter_id=inviter_id,
                referral_id=referral_id,
                amount=3000,
                bonus_type="task",
            )
        )
        await self.commit()
        await self.log(f"Бонус за активность начислен пользователю {inviter_id}")
        return {"success": True, "amount": 3000}

    # -------------------------------------------------
    # 🔹 Проверка и повышение уровня
    # -------------------------------------------------
    async def check_level_up(self, inviter_id: int):
        """
        Проверяет, достиг ли пользователь нового уровня реферальной программы.
        """
        inviter = await self.user_repo.get_by_id(inviter_id)
        if not inviter:
            return {"success": False, "message": "Пользователь не найден"}

        active_referrals = await self.ref_repo.count_active_referrals(inviter_id)
        current_level = inviter.referral_level or 0

        rule = await ReferralRules.can_level_up(active_referrals, current_level)
        if not rule.is_allowed:
            return {"success": False, "message": rule.message}

        inviter.referral_level = rule.metadata.get("new_level")
        await self.commit()

        await self.publish_event(
            ReferralLevelUpEvent(
                inviter_id=inviter_id,
                new_level=inviter.referral_level,
                active_referrals=active_referrals,
            )
        )
        await self.log(f"Пользователь {inviter_id} повысил уровень до {inviter.referral_level}")
        return {"success": True, "new_level": inviter.referral_level}

    # -------------------------------------------------
    # 🔹 Получение списка рефералов
    # -------------------------------------------------
    async def get_user_referrals(self, inviter_id: int, limit: int = 50):
        """
        Возвращает список рефералов пользователя.
        """
        refs = await self.ref_repo.get_by_inviter(inviter_id, limit)
        return [r.as_dict() for r in refs]

    # -------------------------------------------------
    # 🔹 Получение общей статистики
    # -------------------------------------------------
    async def get_global_stats(self):
        """
        Возвращает глобальную статистику по реферальной системе.
        """
        stats = await self.ref_repo.get_stats()
        await self.log("Получена глобальная статистика реферальной программы")
        return stats
