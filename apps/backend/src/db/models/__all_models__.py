"""
Uzinex Boost — ORM Models Loader
=================================

Вспомогательный модуль, обеспечивающий импорт всех ORM-моделей
для Alembic, SQLAlchemy и доменного слоя.

Назначение:
- гарантировать регистрацию всех таблиц в Base.metadata;
- предотвратить проблемы с "неизвестными" моделями при autogenerate;
- использоваться в Alembic env.py, при тестах и инициализации базы.

Импортируется в:
    - db/migrations/env.py
    - domain.services.*
    - core.startup (для валидации схемы)
"""

# Импорт базового класса SQLAlchemy
from db.base import Base

# Импорт всех моделей вручную (чтобы Alembic увидел их при autogenerate)
from db.models.user_model import User
from db.models.balance_model import BalanceTransaction
from db.models.order_model import Order
from db.models.task_model import Task
from db.models.payment_model import Payment
from db.models.referral_model import Referral

__all__ = [
    "Base",
    "User",
    "BalanceTransaction",
    "Order",
    "Task",
    "Payment",
    "Referral",
]


def load_all_models() -> None:
    """
    Принудительно загружает все ORM-модели, чтобы зарегистрировать их
    в `Base.metadata`. Вызывается из Alembic env.py.
    """
    # Это чисто декларативная функция.
    # Импорт выше уже выполняет регистрацию таблиц.
    pass
