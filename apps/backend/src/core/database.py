"""
Uzinex Boost — Database Configuration (Railway Edition)
=======================================================

Настройка асинхронного подключения к PostgreSQL через SQLAlchemy + asyncpg.
Поддерживает SSL (Railway proxy требует защищённое соединение).
"""

from __future__ import annotations

import ssl
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import text
from core.config import settings


# -------------------------------------------------
# 🔹 SSL для Railway PostgreSQL
# -------------------------------------------------
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE


# -------------------------------------------------
# 🔹 Создание асинхронного движка SQLAlchemy
# -------------------------------------------------
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True,
    pool_pre_ping=True,
    connect_args={"ssl": ssl_context},  # Railway требует SSL
)


# -------------------------------------------------
# 🔹 Сессия и базовый класс
# -------------------------------------------------
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

Base = declarative_base()


# -------------------------------------------------
# 🔹 Dependency helper
# -------------------------------------------------
async def get_session() -> AsyncSession:
    """
    Асинхронная зависимость для получения сессии БД (FastAPI Depends).
    """
    async with AsyncSessionLocal() as session:
        yield session


# -------------------------------------------------
# 🔹 Проверка соединения с базой данных
# -------------------------------------------------
async def test_database_connection() -> bool:
    """
    Тестирует соединение с базой данных при старте приложения.
    Возвращает True, если соединение установлено успешно.
    """
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        import logging
        logging.error(f"❌ Database connection test failed: {e}")
        return False
