"""
Uzinex Boost — Core Database Utilities
======================================

Асинхронная интеграция с PostgreSQL через SQLAlchemy.
Используется во всех сервисах, репозиториях и FastAPI зависимостях.
"""

from __future__ import annotations
import logging
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession

from db.base import async_session_factory, engine, Base

logger = logging.getLogger("uzinex.core.database")


# -------------------------------------------------
# 🔹 Получение асинхронной сессии (FastAPI dependency)
# -------------------------------------------------
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency для FastAPI.
    Создаёт новую асинхронную сессию SQLAlchemy и закрывает её по завершении запроса.
    """
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()


# -------------------------------------------------
# 🔹 Тест соединения с базой данных
# -------------------------------------------------
async def test_database_connection() -> bool:
    """
    Проверяет подключение к PostgreSQL (используется при старте приложения).
    """
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("🗄 PostgreSQL connection: ✅ OK")
        return True
    except Exception as e:
        logger.error(f"❌ PostgreSQL connection failed: {e}")
        return False
