"""
Uzinex Boost — Domain Events Package
====================================

Модуль событий домена системы Uzinex Boost.

Назначение:
- централизованная точка регистрации и импорта всех событий;
- экспорт базовых классов и диспетчера;
- обеспечивает удобный доступ к событиям из сервисов и адаптеров.

Архитектура событий:
--------------------
События в Uzinex Boost реализованы по паттерну Domain Event:
  • domain/services генерируют события при изменениях состояния;
  • domain/events описывает их структуру и типизацию;
  • domain/events/dispatcher управляет подписчиками (handlers);
  • adapters реагируют на события (уведомления, интеграции, аналитика).

Пример использования:
---------------------
from domain.events import EventDispatcher, UserRegisteredEvent

event = UserRegisteredEvent(user_id=42, email="user@example.com")
await EventDispatcher.publish(event)
"""

from domain.events.base import DomainEvent
from domain.events.dispatcher import EventDispatcher

# Импортируем основные события домена (по мере добавления)
from domain.events.user_events import UserRegisteredEvent, UserVerifiedEvent
from domain.events.balance_events import BalanceUpdatedEvent
from domain.events.payment_events import PaymentCreatedEvent, PaymentConfirmedEvent
from domain.events.task_events import TaskCompletedEvent
from domain.events.referral_events import ReferralRewardedEvent
from domain.events.order_events import OrderCreatedEvent, OrderCompletedEvent

__all__ = [
    # Базовые элементы
    "DomainEvent",
    "EventDispatcher",

    # Пользователи
    "UserRegisteredEvent",
    "UserVerifiedEvent",

    # Баланс и транзакции
    "BalanceUpdatedEvent",

    # Платежи
    "PaymentCreatedEvent",
    "PaymentConfirmedEvent",

    # Задания
    "TaskCompletedEvent",

    # Рефералы
    "ReferralRewardedEvent",

    # Заказы
    "OrderCreatedEvent",
    "OrderCompletedEvent",
]
