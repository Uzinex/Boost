"""
Uzinex Boost — Balance Events
=============================

События, связанные с балансом и транзакциями пользователей (UZT).

Назначение:
-----------
- отражают все операции с балансом (начисления, списания, переводы);
- используются для аналитики, уведомлений и журналирования;
- обеспечивают асинхронную реакцию на финансовые изменения.

Используется в:
---------------
- domain.services.balance
- domain.services.transaction
- adapters.analytics
- adapters.notifications
"""

from __future__ import annotations
from datetime import datetime
from pydantic import Field

from domain.events.base import DomainEvent


# =================================================
# 🔹 Событие: Баланс изменён
# =================================================
class BalanceUpdatedEvent(DomainEvent):
    """Генерируется при любом изменении баланса пользователя."""

    event_type: str = "balance.updated"
    user_id: int = Field(..., description="ID пользователя, чей баланс изменён")
    amount: float = Field(..., description="Сумма изменения (может быть отрицательной)")
    balance_before: float = Field(..., description="Баланс до изменения")
    balance_after: float = Field(..., description="Баланс после изменения")
    source: str = Field(..., description="Источник операции (task, order, referral, admin и т.д.)")
    transaction_id: int | None = Field(None, description="ID транзакции, связанной с событием")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# =================================================
# 🔹 Событие: Баланс пополнен
# =================================================
class BalanceDepositedEvent(DomainEvent):
    """Генерируется, когда пользователь успешно пополнил баланс."""

    event_type: str = "balance.deposited"
    user_id: int
    amount: float
    payment_id: int
    method: str = Field(..., description="Метод пополнения (click, payme, uzcard, crypto и т.п.)")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# =================================================
# 🔹 Событие: Баланс списан
# =================================================
class BalanceWithdrawnEvent(DomainEvent):
    """Генерируется при списании средств (например, при оплате заказа или выводе средств)."""

    event_type: str = "balance.withdrawn"
    user_id: int
    amount: float
    reason: str = Field(..., description="Причина списания (order, withdraw, fee и т.п.)")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# =================================================
# 🔹 Событие: Средства переведены
# =================================================
class BalanceTransferredEvent(DomainEvent):
    """Генерируется при переводе средств между пользователями."""

    event_type: str = "balance.transferred"
    sender_id: int = Field(..., description="ID отправителя")
    receiver_id: int = Field(..., description="ID получателя")
    amount: float = Field(..., gt=0, description="Сумма перевода")
    currency: str = Field("UZT", description="Тип валюты")
    transaction_id: int | None = Field(None, description="ID связанной транзакции")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# =================================================
# 🔹 Событие: Ошибка при изменении баланса
# =================================================
class BalanceFailedEvent(DomainEvent):
    """Генерируется при ошибке или откате финансовой операции."""

    event_type: str = "balance.failed"
    user_id: int
    amount: float
    error_message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# =================================================
# 🔹 Общие настройки модели
# =================================================
for cls in (
    BalanceUpdatedEvent,
    BalanceDepositedEvent,
    BalanceWithdrawnEvent,
    BalanceTransferredEvent,
    BalanceFailedEvent,
):
    cls.model_config = {"from_attributes": True}
