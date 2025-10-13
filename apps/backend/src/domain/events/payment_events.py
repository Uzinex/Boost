"""
Uzinex Boost — Payment Events
=============================

События, связанные с платежами и финансовыми операциями пользователей.

Назначение:
- фиксируют жизненный цикл платежей (создание, подтверждение, ошибка, возврат);
- позволяют синхронизировать систему баланса, аналитики и уведомлений;
- обеспечивают надёжное событийное взаимодействие между модулями.

Используется в:
- domain.services.payment
- domain.services.balance
- adapters.payments
- adapters.analytics
- adapters.notifications
"""

from __future__ import annotations
from datetime import datetime
from pydantic import Field

from domain.events.base import DomainEvent


# -------------------------------------------------
# 🔹 Событие: Платёж создан
# -------------------------------------------------
class PaymentCreatedEvent(DomainEvent):
    """
    Генерируется при инициализации нового платежа.
    Например, когда пользователь выбирает метод пополнения.
    """

    event_type: str = "payment.created"
    payment_id: int = Field(..., description="ID платежа")
    user_id: int = Field(..., description="ID пользователя, инициировавшего платёж")
    amount: float = Field(..., description="Сумма платежа (UZT)")
    method: str = Field(..., description="Метод оплаты (click, payme, uzcard, crypto, и т.д.)")
    created_at: datetime = Field(default_factory=datetime.utcnow)


# -------------------------------------------------
# 🔹 Событие: Платёж подтверждён
# -------------------------------------------------
class PaymentConfirmedEvent(DomainEvent):
    """
    Генерируется, когда внешний платёжный провайдер подтвердил операцию.
    """

    event_type: str = "payment.confirmed"
    payment_id: int
    user_id: int
    amount: float
    method: str
    provider_txn_id: str | None = Field(None, description="ID транзакции у платёжного провайдера")
    confirmed_at: datetime = Field(default_factory=datetime.utcnow)


# -------------------------------------------------
# 🔹 Событие: Платёж неуспешен / отклонён
# -------------------------------------------------
class PaymentFailedEvent(DomainEvent):
    """
    Генерируется, когда платёж не прошёл (ошибка банка, отмена, недостаточно средств и т.д.).
    """

    event_type: str = "payment.failed"
    payment_id: int
    user_id: int
    amount: float
    method: str
    error_code: str | None = Field(None, description="Код ошибки от платёжной системы")
    error_message: str | None = Field(None, description="Описание ошибки")
    failed_at: datetime = Field(default_factory=datetime.utcnow)


# -------------------------------------------------
# 🔹 Событие: Платёж возвращён (Refund)
# -------------------------------------------------
class PaymentRefundedEvent(DomainEvent):
    """
    Генерируется при возврате средств пользователю.
    """

    event_type: str = "payment.refunded"
    payment_id: int
    user_id: int
    amount: float
    method: str
    reason: str | None = Field(None, description="Причина возврата")
    refunded_at: datetime = Field(default_factory=datetime.utcnow)
