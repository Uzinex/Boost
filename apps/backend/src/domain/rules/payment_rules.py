"""
Uzinex Boost — Payment Rules
============================

Бизнес-правила для управления платежами и их безопасностью.

Назначение:
-----------
Определяет допустимые способы оплаты, лимиты и условия проведения платежей.
Используется для:
- проверки верификации пользователя перед оплатой;
- ограничения методов оплаты;
- контроля минимальной и максимальной суммы операции;
- фильтрации потенциально опасных или подозрительных действий.

Используется в:
- domain.services.payment
- domain.services.balance
- adapters.payments
- api.v1.routes.payment
"""

from __future__ import annotations
from typing import Dict, Any
from datetime import datetime, timedelta

from domain.rules.base import BaseRule
from db.repositories.user_repository import UserRepository


# -------------------------------------------------
# 🔹 Константы политики
# -------------------------------------------------
SUPPORTED_METHODS = ["click", "payme", "uzcard", "crypto"]
VERIFIED_ONLY_METHODS = ["crypto"]
MIN_PAYMENT_AMOUNT = 5_000.0
MAX_PAYMENT_AMOUNT = 10_000_000.0
DAILY_PAYMENT_LIMIT = 20_000_000.0
MAX_PAYMENT_ATTEMPTS_PER_HOUR = 5


# -------------------------------------------------
# 🔹 Правила платежей
# -------------------------------------------------
class PaymentRules(BaseRule):
    """
    Набор правил для проверки допустимости и корректности платежей.
    """

    rule_name = "PaymentRules"

    # -------------------------------------------------
    # 🔸 Проверка допустимости метода оплаты
    # -------------------------------------------------
    @classmethod
    async def validate_method(
        cls,
        user_id: int,
        method: str,
        user_repo: UserRepository,
    ):
        """
        Проверяет, может ли пользователь использовать указанный метод оплаты.
        """
        method = method.lower().strip()

        if method not in SUPPORTED_METHODS:
            return await cls._deny(f"Метод оплаты '{method}' не поддерживается системой")

        user = await user_repo.get_by_id(user_id)
        if not user:
            return await cls._deny("Пользователь не найден")

        if method in VERIFIED_ONLY_METHODS and not user.is_verified:
            return await cls._deny("Для использования этого метода необходимо пройти верификацию")

        return await cls._allow("Метод оплаты разрешён", {"method": method})

    # -------------------------------------------------
    # 🔸 Проверка суммы платежа
    # -------------------------------------------------
    @classmethod
    async def validate_amount(cls, amount: float):
        """
        Проверяет, находится ли сумма в допустимом диапазоне.
        """
        if amount < MIN_PAYMENT_AMOUNT:
            return await cls._deny(f"Минимальная сумма платежа — {MIN_PAYMENT_AMOUNT:.0f} UZT")
        if amount > MAX_PAYMENT_AMOUNT:
            return await cls._deny(f"Превышен лимит: максимум {MAX_PAYMENT_AMOUNT:.0f} UZT")
        return await cls._allow("Сумма платежа корректна", {"amount": amount})

    # -------------------------------------------------
    # 🔸 Проверка лимитов по активности
    # -------------------------------------------------
    @classmethod
    async def check_activity_limits(cls, user_id: int, recent_payments: list):
        """
        Проверяет, не превышены ли лимиты по количеству и сумме платежей за сутки.
        """
        now = datetime.utcnow()
        since = now - timedelta(hours=24)

        recent = [p for p in recent_payments if p.created_at >= since]
        total_sum = sum(p.amount for p in recent)
        if total_sum > DAILY_PAYMENT_LIMIT:
            return await cls._deny("Превышен дневной лимит платежей")

        if len(recent) > MAX_PAYMENT_ATTEMPTS_PER_HOUR:
            return await cls._deny("Слишком много попыток оплат за короткое время")

        return await cls._allow("Платёжная активность в норме", {"payments_today": len(recent)})

    # -------------------------------------------------
    # 🔸 Проверка статуса пользователя
    # -------------------------------------------------
    @classmethod
    async def validate_user_status(cls, user):
        """
        Проверяет, активен ли пользователь и имеет ли право проводить платежи.
        """
        if not user.is_active:
            return await cls._deny("Аккаунт неактивен — операции недоступны")
        if user.is_blocked:
            return await cls._deny("Платёж невозможен: пользователь заблокирован")
        return await cls._allow("Пользователь активен и допущен к оплате")

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
