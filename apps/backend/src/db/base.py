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
from sqlalchemy.orm import DeclarativeBase

# -------------------------------------------------
# 🔹 Базовый класс для всех ORM-моделей
# -------------------------------------------------
class Base(DeclarativeBase):
    """Общий базовый класс для всех SQLAlchemy моделей."""
    pass


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
# Если будет модель transaction_model или другие — добавляются сюда.
# Например:
# from db.models import transaction_model

# -------------------------------------------------
# 🔹 Экспорт metadata
# -------------------------------------------------
metadata = Base.metadata
