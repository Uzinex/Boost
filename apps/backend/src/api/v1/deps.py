"""
Uzinex Boost API v1 — Dependencies
===================================

Централизованные зависимости FastAPI для маршрутов API:
- авторизация пользователей (JWT / Telegram WebApp);
- подключение к БД и Redis;
- инициализация сервисов (domain layer);
- Telegram-клиент и внешние интеграции.

Все эндпоинты /api/v1/routes/* используют эти зависимости через Depends().
"""

from __future__ import annotations

import logging
from fastapi import Depends, HTTPException, status
from typing import AsyncGenerator, Any

from core.database import get_async_session
from core.security import decode_session_token
from domain.services import (
    UserService,
    BalanceService,
    OrderService,
    TaskService,
    PaymentService,
    HealthService,
)
from adapters.cache.redis_cache import RedisCache
from adapters.telegram.client import TelegramClient

logger = logging.getLogger("uzinex.api.deps")


# -------------------------------------------------
# 🔹 Database session
# -------------------------------------------------

async def get_db_session() -> AsyncGenerator:
    """
    Возвращает асинхронную сессию БД.
    Используется всеми сервисами domain-уровня.
    """
    async for session in get_async_session():
        yield session


# -------------------------------------------------
# 🔹 Redis Cache
# -------------------------------------------------

async def get_cache() -> RedisCache:
    """Возвращает экземпляр RedisCache (асинхронное подключение)."""
    cache = RedisCache()
    await cache.connect()
    return cache


# -------------------------------------------------
# 🔹 Telegram Client
# -------------------------------------------------

def get_telegram_client() -> TelegramClient:
    """Создаёт Telegram-клиент для уведомлений и Webhook."""
    return TelegramClient()


# -------------------------------------------------
# 🔹 Current User Authorization
# -------------------------------------------------

async def get_current_user(
    token: str = Depends(decode_session_token),
    user_service: UserService = Depends(lambda: UserService()),
) -> dict[str, Any]:
    """
    Проверяет JWT / session_token и возвращает данные пользователя.
    Используется во всех защищённых эндпоинтах ( /users, /balance, /orders и т.д. ).
    """
    try:
        user_id = token.get("sub")
        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session token")

        user = await user_service.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

        return {
            "id": user.id,
            "username": user.username,
            "first_name": user.first_name,
            "language": user.language,
        }
    except Exception as e:
        logger.warning(f"[Auth] Unauthorized access attempt: {e}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")


# -------------------------------------------------
# 🔹 Domain Services
# -------------------------------------------------

def get_user_service() -> UserService:
    """Возвращает экземпляр UserService."""
    return UserService()


def get_balance_service() -> BalanceService:
    """Возвращает экземпляр BalanceService."""
    return BalanceService()


def get_order_service() -> OrderService:
    """Возвращает экземпляр OrderService."""
    return OrderService()


def get_task_service() -> TaskService:
    """Возвращает экземпляр TaskService."""
    return TaskService()


def get_payment_service() -> PaymentService:
    """Возвращает экземпляр PaymentService."""
    return PaymentService()


def get_health_service() -> HealthService:
    """Возвращает экземпляр HealthService (для /system/health)."""
    return HealthService()
