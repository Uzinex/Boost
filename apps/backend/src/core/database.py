"""
Uzinex Boost Core — Database Layer
===================================

Асинхронная конфигурация PostgreSQL для Boost v2.0.

Назначение:
- создание асинхронного SQLAlchemy engine;
- фабрика сессий `get_async_session`;
- интеграция с Alembic (миграции);
- безопасное управление транзакциями (commit/rollback);
- логирование подключения.

Использует:
    - asyncpg
    - SQLAlchemy 2.x async
"""

from __future__ import annotations

import logging
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base
from contextlib import asynccontextmanager

from core import settings

# -------------------------------------------------
# 🔹 Логгер и база моделей
# -------------------------------------------------

logger = logging.getLogger("uzinex.core.database")
Base = declarative_base()

# -------------------------------------------------
# 🔹 Создание асинхронного движка
# -------------------------------------------------

DATABASE_URL = settings.DATABASE_URL

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    future=True,
)

# -------------------------------------------------
# 🔹 Фабрика сессий (sessionmaker)
# -------------------------------------------------

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


# -------------------------------------------------
# 🔹 Dependency для FastAPI
# -------------------------------------------------

@asynccontextmanager
async def get_async_session() -> AsyncSession:
    """
    Асинхронный генератор сессии БД.
    Используется во всех сервисах (domain layer) и зависимостях API.
    """
    session = AsyncSessionLocal()
    try:
        yield session
        await session.commit()
    except Exception as e:
        await session.rollback()
        logger.exception(f"[DB] Transaction rollback due to: {e}")
        raise
    finally:
        await session.close()


# -------------------------------------------------
# 🔹 Проверка подключения (HealthCheck)
# -------------------------------------------------

async def test_database_connection() -> bool:
    """
    Проверяет соединение с базой данных (используется в /system/health).
    Возвращает True при успешном подключении.
    """
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"[DB] Connection test failed: {e}")
        return False


# -------------------------------------------------
# 🔹 Утилита для Alembic
# -------------------------------------------------

def get_engine() -> any:
    """
    Возвращает SQLAlchemy engine для Alembic и административных задач.
    """
    return engine
