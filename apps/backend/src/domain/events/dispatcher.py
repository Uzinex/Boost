"""
Uzinex Boost — Event Dispatcher
===============================

Центральный диспетчер событий (Event Bus) домена Uzinex Boost.

Назначение:
- управляет подписчиками и обработчиками событий;
- обеспечивает асинхронную публикацию и доставку;
- служит точкой интеграции между domain и adapters слоями.

Паттерн: Event Bus / Pub-Sub
-----------------------------
• domain/services публикуют события через EventDispatcher.publish(event)
• обработчики (handlers) подписываются на конкретные типы событий
• adapters реагируют на эти события (уведомления, аналитика, интеграции и т.д.)

Используется в:
- domain.services.*
- adapters.notifications
- adapters.analytics
- adapters.logging
"""

from __future__ import annotations
import asyncio
from typing import Any, Awaitable, Callable, Dict, List, Type, Union
from loguru import logger

from domain.events.base import DomainEvent


# -------------------------------------------------
# 🔹 Типы
# -------------------------------------------------
EventHandler = Union[Callable[[DomainEvent], Awaitable[None]], Callable[[DomainEvent], None]]


# -------------------------------------------------
# 🔹 Диспетчер событий
# -------------------------------------------------
class EventDispatcher:
    """
    Асинхронный диспетчер событий (Event Bus) для Uzinex Boost.
    """

    _subscribers: Dict[str, List[EventHandler]] = {}

    # -------------------------------------------------
    # 🔹 Подписка
    # -------------------------------------------------
    @classmethod
    def subscribe(cls, event_type: str, handler: EventHandler) -> None:
        """
        Регистрирует обработчик на определённый тип события.
        """
        if event_type not in cls._subscribers:
            cls._subscribers[event_type] = []
        cls._subscribers[event_type].append(handler)
        logger.debug(f"[EventDispatcher] Subscribed handler '{handler.__name__}' to event '{event_type}'")

    # -------------------------------------------------
    # 🔹 Публикация события
    # -------------------------------------------------
    @classmethod
    async def publish(cls, event: DomainEvent) -> None:
        """
        Публикует событие всем подписчикам.
        """
        handlers = cls._subscribers.get(event.event_type, [])
        if not handlers:
            logger.debug(f"[EventDispatcher] No handlers for event '{event.event_type}'")
            return

        logger.info(f"[EventDispatcher] Publishing event '{event.event_type}' → {len(handlers)} handler(s)")

        # Асинхронно вызываем всех подписчиков
        tasks = []
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    tasks.append(asyncio.create_task(handler(event)))
                else:
                    handler(event)
            except Exception as e:
                logger.error(f"[EventDispatcher] Error executing handler {handler.__name__}: {e}")

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    # -------------------------------------------------
    # 🔹 Удалить подписку
    # -------------------------------------------------
    @classmethod
    def unsubscribe(cls, event_type: str, handler: EventHandler) -> None:
        """
        Удаляет обработчик из списка подписчиков.
        """
        handlers = cls._subscribers.get(event_type, [])
        if handler in handlers:
            handlers.remove(handler)
            logger.debug(f"[EventDispatcher] Unsubscribed '{handler.__name__}' from event '{event_type}'")

    # -------------------------------------------------
    # 🔹 Очистить все подписки
    # -------------------------------------------------
    @classmethod
    def clear(cls) -> None:
        """
        Удаляет все подписки (используется в тестах).
        """
        cls._subscribers.clear()
        logger.debug("[EventDispatcher] All event subscriptions cleared")

    # -------------------------------------------------
    # 🔹 Вспомогательные методы
    # -------------------------------------------------
    @classmethod
    def get_subscribers(cls) -> Dict[str, List[str]]:
        """
        Возвращает текущий список подписчиков (для диагностики/отладки).
        """
        return {etype: [h.__name__ for h in handlers] for etype, handlers in cls._subscribers.items()}
