"""
Uzinex Boost — Base Service
===========================

Базовый класс для всех бизнес-сервисов Uzinex Boost v2.0.

Назначение:
-----------
Определяет общие принципы для сервисов:
- инициализацию сессии и репозиториев;
- централизованное логирование;
- обработку событий и ошибок;
- интеграцию с доменными правилами (`domain.rules`);
- реактивное взаимодействие с событиями (`domain.events`).

Используется как родительский класс для:
- UserService
- BalanceService
- PaymentService
- OrderService
- TaskService
- ReferralService
"""

from __future__ import annotations
from typing import Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from domain.events.dispatcher import EventDispatcher


# -------------------------------------------------
# 🔹 Базовый сервис
# -------------------------------------------------
class BaseService:
    """
    Абстрактный базовый класс для всех сервисов системы.

    Каждый сервис имеет:
    - доступ к асинхронной сессии SQLAlchemy;
    - встроенный логгер;
    - методы публикации событий;
    - унифицированную обработку ошибок.
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.logger = logger.bind(service=self.__class__.__name__)

    # -------------------------------------------------
    # 🔸 Логирование действий
    # -------------------------------------------------
    async def log(self, message: str, **kwargs: Any):
        """
        Унифицированное логирование действий сервиса.
        """
        self.logger.info(f"{self.__class__.__name__}: {message}", **kwargs)

    # -------------------------------------------------
    # 🔸 Публикация событий
    # -------------------------------------------------
    async def publish_event(self, event: Any):
        """
        Отправляет доменное событие в шину событий (Event Bus).
        """
        await EventDispatcher.publish(event)
        self.logger.debug(f"Event published: {event.event_type} ({event.__class__.__name__})")

    # -------------------------------------------------
    # 🔸 Безопасное выполнение операции
    # -------------------------------------------------
    async def safe_execute(self, func, *args, **kwargs) -> Optional[Any]:
        """
        Безопасное выполнение операции с отловом ошибок и логированием.
        Возвращает результат или None при ошибке.
        """
        try:
            result = await func(*args, **kwargs)
            return result
        except Exception as e:
            self.logger.exception(f"Error in {self.__class__.__name__}: {e}")
            await self.session.rollback()
            return None

    # -------------------------------------------------
    # 🔸 Коммит транзакции
    # -------------------------------------------------
    async def commit(self):
        """
        Подтверждает изменения в сессии.
        """
        try:
            await self.session.commit()
            self.logger.debug("Session committed successfully.")
        except Exception as e:
            self.logger.exception(f"Commit failed: {e}")
            await self.session.rollback()

    # -------------------------------------------------
    # 🔸 Откат транзакции
    # -------------------------------------------------
    async def rollback(self):
        """
        Откатывает все несохранённые изменения.
        """
        await self.session.rollback()
        self.logger.warning("Session rolled back.")
