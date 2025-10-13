"""
Uzinex Boost — Referral Rules
=============================

Бизнес-правила, регулирующие работу реферальной системы.

Назначение:
-----------
Определяет, кто, когда и при каких условиях получает бонусы и уровни:
- проверка лимитов по приглашениям;
- условия получения бонусов;
- минимальные активности реферала;
- контроль злоупотреблений и фрода.

Используется в:
- domain.services.referral
- domain.services.balance
- domain.services.analytics
- adapters.notifications
- api.v1.routes.referral
"""

from __future__ import annotations
from datetime import datetime, timedelta
from typing import Dict, Any

from domain.rules.base import BaseRule


# -------------------------------------------------
# 🔹 Константы политики реферальной системы
# -------------------------------------------------
MAX_REFERRALS_PER_USER = 100                # максимальное количество прямых рефералов
MIN_REFERRAL_ACTIVITY_DAYS = 3              # минимальная активность реферала до бонуса
REFERRAL_BONUS_FOR_SIGNUP = 5_000.0         # бонус за регистрацию приглашённого
REFERRAL_BONUS_FOR_TASK = 3_000.0           # бонус за выполнение задания рефералом
LEVEL_UP_REQUIREMENTS = {                   # количество активных рефералов для достижения уровня
    1: 5,
    2: 15,
    3: 30,
    4: 60,
}
MAX_REFERRAL_BONUS_PER_DAY = 50_000.0       # лимит бонусов за день
BONUS_COOLDOWN = timedelta(hours=12)        # минимальный интервал между бонусами


# -------------------------------------------------
# 🔹 Правила реферальной системы
# -------------------------------------------------
class ReferralRules(BaseRule):
    """
    Набор бизнес-правил, связанных с начислением и управлением реферальными бонусами.
    """

    rule_name = "ReferralRules"

    # -------------------------------------------------
    # 🔸 Проверка лимита по приглашениям
    # -------------------------------------------------
    @classmethod
    async def can_invite(cls, inviter_id: int, total_referrals: int):
        """
        Проверяет, может ли пользователь пригласить ещё одного участника.
        """
        if total_referrals >= MAX_REFERRALS_PER_USER:
            return await cls._deny(f"Превышен лимит приглашённых ({MAX_REFERRALS_PER_USER})")
        return await cls._allow("Можно пригласить нового участника", {"referrals": total_referrals})

    # -------------------------------------------------
    # 🔸 Проверка права на бонус за регистрацию
    # -------------------------------------------------
    @classmethod
    async def can_receive_signup_bonus(cls, referral_joined_at: datetime):
        """
        Проверяет, может ли пользователь получить бонус за регистрацию реферала.
        """
        now = datetime.utcnow()
        if now - referral_joined_at < timedelta(hours=1):
            return await cls._deny("Бонус за регистрацию начисляется не сразу, подождите немного")
        return await cls._allow("Бонус за регистрацию разрешён")

    # -------------------------------------------------
    # 🔸 Проверка права на бонус за активность реферала
    # -------------------------------------------------
    @classmethod
    async def can_receive_task_bonus(cls, referral_first_task_date: datetime):
        """
        Проверяет, можно ли начислить бонус за активность реферала.
        """
        if datetime.utcnow() - referral_first_task_date < timedelta(days=MIN_REFERRAL_ACTIVITY_DAYS):
            return await cls._deny(f"Реферал должен быть активен не менее {MIN_REFERRAL_ACTIVITY_DAYS} дней")
        return await cls._allow("Бонус за активность разрешён")

    # -------------------------------------------------
    # 🔸 Проверка лимита бонусов за день
    # -------------------------------------------------
    @classmethod
    async def check_daily_bonus_limit(cls, today_bonus_sum: float):
        """
        Проверяет, не превышен ли дневной лимит бонусов.
        """
        if today_bonus_sum >= MAX_REFERRAL_BONUS_PER_DAY:
            return await cls._deny("Достигнут лимит начислений бонусов за день")
        return await cls._allow("Начисление бонуса разрешено", {"today_bonus_sum": today_bonus_sum})

    # -------------------------------------------------
    # 🔸 Проверка интервала между бонусами
    # -------------------------------------------------
    @classmethod
    async def check_bonus_cooldown(cls, last_bonus_time: datetime | None):
        """
        Проверяет, прошло ли достаточно времени между начислениями.
        """
        if last_bonus_time and datetime.utcnow() - last_bonus_time < BONUS_COOLDOWN:
            return await cls._deny("Следующий бонус можно получить через несколько часов")
        return await cls._allow("Можно начислить новый бонус")

    # -------------------------------------------------
    # 🔸 Проверка достижения нового уровня
    # -------------------------------------------------
    @classmethod
    async def can_level_up(cls, active_referrals: int, current_level: int):
        """
        Проверяет, достиг ли пользователь нового уровня реферальной программы.
        """
        next_level = current_level + 1
        required = LEVEL_UP_REQUIREMENTS.get(next_level)
        if not required:
            return await cls._deny("Достигнут максимальный уровень реферальной программы")

        if active_referrals < required:
            return await cls._deny(
                f"Для перехода на уровень {next_level} требуется {required} активных рефералов"
            )
        return await cls._allow("Переход на новый уровень разрешён", {"new_level": next_level})

    # -------------------------------------------------
    # 🔹 Вспомогательные методы
    # -------------------------------------------------
    @classmethod
    async def _allow(cls, message: str, meta: Dict[str, Any] | None = None):
        return await cls._result(True, message, meta)

    @classmethod
    async def _deny(cls, message: str, meta: Dict[str, Any] | None = None):
        return await cls._result(False, message, meta)

    @classmethod
    async def _result(cls, allowed: bool, message: str, meta: Dict[str, Any] | None = None):
        from domain.rules.base import RuleResult
        return RuleResult(
            is_allowed=allowed,
            message=message,
            rule_name=cls.rule_name,
            metadata=meta or {},
        )
