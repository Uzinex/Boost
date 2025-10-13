"""
Uzinex Boost — Database Base Configuration
==========================================

Базовая конфигурация ORM и импорт всех моделей для Alembic и репозиториев.
"""

from __future__ import annotations
from sqlalchemy.orm import declarative_base

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
# from db.models import transaction_model  # добавится позже

# -------------------------------------------------
# 🔹 Экспорт metadata
# -------------------------------------------------
metadata = Base.metadata
