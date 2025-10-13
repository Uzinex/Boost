"""
Uzinex Boost — Balance Rules
============================

Бизнес-правила, регулирующие операции с балансом пользователей (UZT).

Назначение:
-----------
Определяют допустимость финансовых действий:
- проверка лимитов вывода и пополнения;
- минимальная и максимальная сумма операции;
- ограничения по частоте и статусу пользователя;
- защита от злоупотреблений и фрода.

Используется в:
- domain.services.balance
- domain.services.transaction
- adapters.payments
- api.v1.routes.balance
"""

from __future__ import annotations
from datetime import datetime, timedelta
from typing import Dict, Any

from domain.rules.base import BaseRule
from db.repositories.transaction_repository import TransactionRepository


# -------------------------------------------------
# 🔹 Константы политики
# -------------------------------------------------
MIN_WITHDRAW_AMOUNT = 10_000.0      # минимальная сумма вывода (UZT)
MAX_WITHDRAW_AMOUNT = 5_000_000.0   # максимальная сумма за одну операцию
MAX_DAILY_WITHDRAW_COUNT = 3        # максимум операций вывода в сутки
MAX_DAILY_WITHDRAW_SUM = 10_000_000.0  # лимит общей суммы выводов в день
MIN_DEPOSIT_AMOUNT = 5_000.0        # минимальная сумма пополнения
COOLDOWN_BETWEEN_TX = timedelta(seconds=30)  # пауза между транзакциями


# -------------------------------------------------
# 🔹 Правила баланса
# -------------------------------------------------
class BalanceRules(BaseRule):
    """
    Набор правил для проверки допустимости операций с балансом.
    """

    rule_name = "BalanceRules"

    # -------------------------------------------------
    # 🔸 Проверка вывода средств
    # -------------------------------------------------
    @classmethod
    async def can_withdraw(
        cls,
        user_id: int,
        amount: float,
        transaction_repo: TransactionRepository,
    ):
        """
        Проверяет, может ли пользователь вывести указанную сумму.
        """
        # 1️⃣ Минимальная и максимальная сумма
        if amount < MIN_WITHDRAW_AMOUNT:
            return await cls._deny(f"Минимальная сумма вывода — {MIN_WITHDRAW_AMOUNT:.0f} UZT")
        if amount > MAX_WITHDRAW_AMOUNT:
            return await cls._deny(f"Сумма превышает лимит {MAX_WITHDRAW_AMOUNT:.0f} UZT за одну операцию")

        # 2️⃣ Проверка частоты операций
        now = datetime.utcnow()
        since = now - timedelta(hours=24)
        recent_tx = await transaction_repo.get_by_user(user_id)
        recent_withdraws = [tx for tx in recent_tx if tx.type == "withdraw" and tx.created_at >= since]

        if len(recent_withdraws) >= MAX_DAILY_WITHDRAW_COUNT:
            return await cls._deny("Превышено количество операций вывода за сутки")

        total_withdraw_sum = sum(abs(tx.amount) for tx in recent_withdraws)
        if total_withdraw_sum + amount > MAX_DAILY_WITHDRAW_SUM:
            return await cls._deny("Превышен дневной лимит суммы выводов")

        # 3️⃣ Проверка последней операции (anti-spam)
        if recent_tx:
            last_tx = max(recent_tx, key=lambda t: t.created_at)
            if (now - last_tx.created_at) < COOLDOWN_BETWEEN_TX:
                return await cls._deny("Слишком частые операции. Попробуйте через 30 секунд")

        # ✅ Всё хорошо
        return await cls._allow("Вывод разрешён", {"amount": amount})

    # -------------------------------------------------
    # 🔸 Проверка пополнения
    # -------------------------------------------------
    @classmethod
    async def can_deposit(cls, amount: float):
        """
        Проверяет корректность суммы пополнения.
        """
        if amount < MIN_DEPOSIT_AMOUNT:
            return await cls._deny(f"Минимальная сумма пополнения — {MIN_DEPOSIT_AMOUNT:.0f} UZT")
        if amount > MAX_WITHDRAW_AMOUNT:
            return await cls._deny(f"Превышен лимит пополнения — {MAX_WITHDRAW_AMOUNT:.0f} UZT")
        return await cls._allow("Пополнение разрешено", {"amount": amount})

    # -------------------------------------------------
    # 🔸 Проверка перевода между пользователями
    # -------------------------------------------------
    @classmethod
    async def can_transfer(cls, sender_id: int, receiver_id: int, amount: float):
        """
        Проверяет допустимость перевода между пользователями.
        """
        if sender_id == receiver_id:
            return await cls._deny("Невозможно перевести средства самому себе")
        if amount <= 0:
            return await cls._deny("Сумма перевода должна быть больше нуля")
        if amount < 1000:
            return await cls._deny("Минимальная сумма перевода — 1000 UZT")
        return await cls._allow("Перевод разрешён", {"sender_id": sender_id, "receiver_id": receiver_id})

    # -------------------------------------------------
    # 🔹 Вспомогательные методы
    # -------------------------------------------------
    @classmethod
    async def _allow(cls, message: str, meta: Dict[str, Any] | None = None):
        return await super().evaluate_result(True, message, meta)

    @classmethod
    async def _deny(cls, message: str, meta: Dict[str, Any] | None = None):
        return await super().evaluate_result(False, message, meta)

    @classmethod
    async def evaluate_result(cls, allowed: bool, message: str, meta: Dict[str, Any] | None = None):
        from domain.rules.base import RuleResult
        return RuleResult(is_allowed=allowed, message=message, rule_name=cls.rule_name, metadata=meta or {})
