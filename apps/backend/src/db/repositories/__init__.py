"""
Uzinex Boost — Database Repositories
=====================================

Пакет репозиториев (Data Access Layer, DAL) для работы с базой данных.

Назначение:
- обеспечивает доступ к данным на уровне ORM (SQLAlchemy);
- реализует CRUD-операции и специализированные запросы;
- отделяет бизнес-логику от низкоуровневого взаимодействия с БД.

Используется в:
- domain.services.*
- api.v1.routes.*
- core.startup (проверка зависимостей)
"""

from __future__ import annotations

# Импорт базового класса
from .base import BaseRepository

# Импорт конкретных репозиториев
from .user_repository import UserRepository
from .order_repository import OrderRepository
from .task_repository import TaskRepository
from .payment_repository import PaymentRepository
from .transaction_repository import TransactionRepository
from .referral_repository import ReferralRepository


__all__ = [
    "BaseRepository",
    "UserRepository",
    "OrderRepository",
    "TaskRepository",
    "PaymentRepository",
    "TransactionRepository",
    "ReferralRepository",
]
