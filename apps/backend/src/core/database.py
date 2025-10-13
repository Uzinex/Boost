"""
Uzinex Boost — Core Database Utilities
======================================

Асинхронная интеграция с PostgreSQL через SQLAlchemy.
"""

from __future__ import annotations
import logging
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from core.config import settings
from db.base import Base  # безопасно, т.к. теперь db/base не тянет core обратно

logger = logging.getLogger("uzinex.core.database")

# -------------------------------------------------
# 🔹 Асинхронный движок
# -------------------------------------------------
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
    pool_pre_ping=True,
)

# -------------------------------------------------
# 🔹 Сессия
# -------------------------------------------------
async_session_factory = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession,
)

# -------------------------------------------------
# 🔹 Зависимости
# -------------------------------------------------
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency для FastAPI — создаёт сессию и автоматически закрывает её."""
    async with async_session_factory() as session:
        yield session


# -------------------------------------------------
# 🔹 Health-check для старта
# -------------------------------------------------
async def test_database_connection() -> bool:
    """Проверяет соединение с базой данных при старте приложения."""
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("🗄 PostgreSQL connection: ✅ OK")
        return True
    except Exception as e:
        logger.error(f"❌ PostgreSQL connection failed: {e}")
        return False
