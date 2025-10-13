"""
Uzinex Boost Core — Dependencies
=================================

Базовые зависимости ядра, используемые на уровне инфраструктуры:
- доступ к настройкам (`get_settings`);
- подключение к БД (`get_db`);
- доступ к Redis / Cache (`get_cache`);
- логгер (`get_logger`).

Отличие от api/v1/deps.py:
    → этот модуль не зависит от FastAPI (минимум импортов),
      чтобы его можно было безопасно использовать в CLI, Celery, Alembic и тестах.
"""

from __future__ import annotations

import logging
from typing import AsyncGenerator

from core import settings, get_logger
from core.database import get_async_session
from adapters.cache.redis_cache import RedisCache


# -------------------------------------------------
# 🔹 Настройки
# -------------------------------------------------

def get_settings():
    """
    Возвращает глобальные настройки приложения.
    Используется при инициализации сервисов, фоновых задач и тестов.
    """
    return settings


# -------------------------------------------------
# 🔹 Логгер
# -------------------------------------------------

def get_logger_instance(name: str = "uzinex.core") -> logging.Logger:
    """
    Возвращает именованный логгер.
    Используется сервисами и адаптерами вне FastAPI.
    """
    return get_logger(name)


# -------------------------------------------------
# 🔹 Асинхронная сессия БД
# -------------------------------------------------

async def get_db() -> AsyncGenerator:
    """
    Асинхронная зависимость для доступа к PostgreSQL.
    Поддерживает автоматический commit / rollback.
    """
    async for session in get_async_session():
        yield session


# -------------------------------------------------
# 🔹 Redis Cache
# -------------------------------------------------

async def get_cache() -> RedisCache:
    """
    Возвращает экземпляр RedisCache для внутренних сервисов и воркеров.
    """
    cache = RedisCache()
    await cache.connect()
    return cache


# -------------------------------------------------
# 🔹 Проверка системных зависимостей
# -------------------------------------------------

async def system_health_check() -> dict[str, bool]:
    """
    Выполняет тест доступности системных компонентов (DB + Redis).
    Используется при старте приложения или в /system/health.
    """
    db_ok = False
    redis_ok = False

    try:
        async for session in get_async_session():
            await session.execute("SELECT 1")
            db_ok = True
            break
    except Exception as e:
        get_logger_instance().error(f"[Core] Database check failed: {e}")

    try:
        cache = RedisCache()
        redis_ok = await cache.ping()
    except Exception as e:
        get_logger_instance().error(f"[Core] Redis check failed: {e}")

    return {"database": db_ok, "redis": redis_ok}
