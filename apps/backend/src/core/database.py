"""
Uzinex Boost — Database Configuration (Railway Edition)
=======================================================

Настройка асинхронного подключения к PostgreSQL через SQLAlchemy + asyncpg.
Поддерживает SSL (Railway proxy требует защищённое соединение).

Используется во всех модулях backend-системы:
- core.deps
- domain.services.*
- db.migrations (через Alembic)
"""

from __future__ import annotations

import ssl
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
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
    settings.DATABASE_URL,           # пример: postgresql+asyncpg://user:pass@host:port/db
    echo=False,                      # отключаем SQL-логи в продакшене
    future=True,
    pool_pre_ping=True,              # проверка соединения перед использованием
    connect_args={"ssl": ssl_context}  # Railway требует SSL
)


# -------------------------------------------------
# 🔹 SessionMaker (асинхронный)
# -------------------------------------------------
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# -------------------------------------------------
# 🔹 Базовый класс моделей
# -------------------------------------------------
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
