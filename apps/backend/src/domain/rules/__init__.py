"""
Uzinex Boost — Domain Rules Package
===================================

Модуль бизнес-правил (Domain Rules) системы Uzinex Boost.

Назначение:
-----------
• Описывает условия, ограничения и политики платформы;
• Отделяет бизнес-логику от её правил и политик;
• Используется сервисами для проверки корректности действий перед их выполнением.

Архитектура:
------------
Каждое правило реализует базовый класс `BaseRule` и возвращает `RuleResult`.

Пример применения:
------------------
from domain.rules.balance_rules import BalanceRules

if not await BalanceRules.can_withdraw(user_id, amount):
    raise RuleViolation("Минимальная сумма вывода 10 000 UZT")

Используется в:
---------------
- domain.services.user
- domain.services.balance
- domain.services.order
- domain.services.payment
- domain.services.referral
- domain.services.task
"""

from domain.rules.base import BaseRule, RuleResult

__all__ = [
    "BaseRule",
    "RuleResult",
]
