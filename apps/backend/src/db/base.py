"""
Uzinex Boost — Database Base Configuration
==========================================

Базовая конфигурация ORM и импорт всех моделей для Alembic и репозиториев.

Назначение:
- определяет SQLAlchemy Base для всех моделей;
- централизует импорт моделей для автоматической регистрации в metadata;
- используется Alembic (env.py) при миграциях;
- облегчает доступ к моделям из других модулей.

Используется в:
- db.database (инициализация движка и сессии)
- db.migrations.env.py
- domain.services.*
- db.repositories.*
"""

from __future__ import annotations
import logging
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base

from core.config import settings

logger = logging.getLogger("uzinex.db.base")

# -------------------------------------------------
# 🔹 Базовый класс моделей
# -------------------------------------------------
Base = declarative_base()

# -------------------------------------------------
# 🔹 Импорт всех моделей проекта для регистрации в metadata
# -------------------------------------------------
from db.models import (
    user_model,
    balance_model,
    order_model,
    payment_model,
    referral_model,
    task_model,
)
# from db.models import transaction_model  # добавится позже при необходимости

# -------------------------------------------------
# 🔹 Экспорт metadata
# -------------------------------------------------
metadata = Base.metadata

# -------------------------------------------------
# 🔹 Асинхронный движок и фабрика сессий
# -------------------------------------------------
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
    pool_pre_ping=True,
)

async_session_factory = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession,
)

logger.info("✅ Database base module initialized (engine + session factory ready)")
