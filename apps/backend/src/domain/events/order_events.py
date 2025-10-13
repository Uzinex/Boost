"""
Uzinex Boost — Order Events
===========================

События, связанные с заказами и их жизненным циклом в системе Uzinex Boost.

Назначение:
- фиксируют ключевые этапы жизненного цикла заказов;
- служат триггерами для транзакций, аналитики и уведомлений;
- обеспечивают прозрачность и реактивность бизнес-процессов.

Используется в:
- domain.services.order
- domain.services.payment
- domain.services.balance
- adapters.analytics
- adapters.notifications
"""

from __future__ import annotations
from datetime import datetime
from pydantic import Field

from domain.events.base import DomainEvent


# -------------------------------------------------
# 🔹 Событие: Заказ создан
# -------------------------------------------------
class OrderCreatedEvent(DomainEvent):
    """
    Генерируется при создании нового заказа заказчиком.
    """

    event_type: str = "order.created"
    order_id: int = Field(..., description="ID заказа")
    client_id: int = Field(..., description="ID заказчика")
    performer_id: int | None = Field(None, description="ID исполнителя, если уже выбран")
    title: str = Field(..., description="Название или описание заказа")
    price: float = Field(..., description="Стоимость заказа (UZT)")
    created_at: datetime = Field(default_factory=datetime.utcnow)


# -------------------------------------------------
# 🔹 Событие: Заказ принят исполнителем
# -------------------------------------------------
class OrderAcceptedEvent(DomainEvent):
    """
    Генерируется, когда исполнитель подтверждает участие в заказе.
    """

    event_type: str = "order.accepted"
    order_id: int
    performer_id: int
    accepted_at: datetime = Field(default_factory=datetime.utcnow)


# -------------------------------------------------
# 🔹 Событие: Заказ выполнен исполнителем
# -------------------------------------------------
class OrderCompletedEvent(DomainEvent):
    """
    Генерируется, когда исполнитель завершает выполнение заказа.
    """

    event_type: str = "order.completed"
    order_id: int
    performer_id: int
    price: float = Field(..., description="Оплата за выполнение заказа")
    completed_at: datetime = Field(default_factory=datetime.utcnow)


# -------------------------------------------------
# 🔹 Событие: Заказ подтверждён заказчиком
# -------------------------------------------------
class OrderConfirmedEvent(DomainEvent):
    """
    Генерируется, когда заказчик подтверждает выполнение заказа.
    """

    event_type: str = "order.confirmed"
    order_id: int
    client_id: int
    performer_id: int
    confirmed_at: datetime = Field(default_factory=datetime.utcnow)


# -------------------------------------------------
# 🔹 Событие: Заказ отменён
# -------------------------------------------------
class OrderCancelledEvent(DomainEvent):
    """
    Генерируется, когда заказ отменяется (клиентом, исполнителем или системой).
    """

    event_type: str = "order.cancelled"
    order_id: int
    cancelled_by: int = Field(..., description="ID пользователя, отменившего заказ")
    reason: str | None = Field(None, description="Причина отмены")
    refunded: bool = Field(default=False, description="Возврат средств выполнен?")
    cancelled_at: datetime = Field(default_factory=datetime.utcnow)


# -------------------------------------------------
# 🔹 Событие: Платёж за заказ подтверждён
# -------------------------------------------------
class OrderPaidEvent(DomainEvent):
    """
    Генерируется, когда платёж за заказ успешно проведён.
    """

    event_type: str = "order.paid"
    order_id: int
    payment_id: int
    client_id: int
    performer_id: int | None = Field(None, description="ID исполнителя (если известен)")
    amount: float = Field(..., description="Сумма платежа")
    paid_at: datetime = Field(default_factory=datetime.utcnow)


# -------------------------------------------------
# 🔹 Событие: Исполнитель получил оплату
# -------------------------------------------------
class OrderRewardedEvent(DomainEvent):
    """
    Генерируется, когда исполнителю начислены средства за выполненный заказ.
    """

    event_type: str = "order.rewarded"
    order_id: int
    performer_id: int
    amount: float
    balance_before: float
    balance_after: float
    transaction_id: int | None = Field(None, description="ID транзакции начисления")
    rewarded_at: datetime = Field(default_factory=datetime.utcnow)
