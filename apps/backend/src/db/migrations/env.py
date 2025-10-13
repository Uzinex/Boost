"""
Uzinex Boost — Alembic Environment
===================================

Конфигурация окружения Alembic для миграций PostgreSQL.

Функции:
- подключение к базе данных через core.database.engine;
- загрузка metadata из domain.models;
- поддержка offline / online режимов;
- интеграция с core.config.settings (DATABASE_URL).

Используется при командах:
    alembic revision --autogenerate -m "init"
    alembic upgrade head
    alembic downgrade -1
"""

from __future__ import annotations

import sys
import asyncio
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

# --- Добавляем путь до приложения ---
BASE_DIR = Path(__file__).resolve().parents[3]
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

# --- Импорты проекта ---
from core import settings  # noqa
from core.database import Base  # noqa
from domain import models  # noqa (для загрузки всех ORM моделей)
from core.logging import setup_logging

# --- Настройка логирования Alembic ---
fileConfig(context.config.config_file_name)
setup_logging()
logger = context.get_context().opts.get("logger", None)

# --- Конфигурация Alembic ---
target_metadata = Base.metadata
DATABASE_URL = settings.DATABASE_URL


# -------------------------------------------------
# 🔹 OFFLINE режим (генерация SQL без подключения)
# -------------------------------------------------

def run_migrations_offline() -> None:
    """Запускает миграции в offline-режиме (без подключения к БД)."""
    url = DATABASE_URL
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


# -------------------------------------------------
# 🔹 ONLINE режим (реальное выполнение миграций)
# -------------------------------------------------

def do_run_migrations(connection: Connection) -> None:
    """Выполняет миграции в активном подключении."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Создаёт асинхронное подключение и выполняет миграции."""
    connectable: AsyncEngine = create_async_engine(DATABASE_URL, poolclass=pool.NullPool)

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


# -------------------------------------------------
# 🔹 Точка входа
# -------------------------------------------------

if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
