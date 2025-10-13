"""
Uzinex Boost — Database Models
===============================

Пакет ORM-моделей SQLAlchemy для проекта Boost v2.0.

Назначение:
- централизует импорт всех моделей;
- обеспечивает регистрацию metadata для Alembic;
- связывает domain-уровень с инфраструктурой базы данных.

Используется:
- Alembic (env.py)
- domain.services.*
- FastAPI CRUD-операции
"""

from __future__ import annotations

from core.database import Base

# Импорт всех моделей (в строгом порядке для Alembic)
from .user_model import User
from .balance_model import BalanceTransaction
from .order_model import Order
from .task_model import Task
from .payment_model import Payment
from .referral_model import Referral

__all__ = [
    "Base",
    "User",
    "BalanceTransaction",
    "Order",
    "Task",
    "Payment",
    "Referral",
]
