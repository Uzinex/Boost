"""
Uzinex Boost — Domain Services Package
======================================

Сервисы прикладного уровня (application / domain layer):
- инкапсулируют бизнес-логику
- координируют работу правил (rules) и репозиториев (repositories)
- не содержат зависимостей от FastAPI (чистая логика)

Сервисы:
- HealthService — системная проверка статуса
- StatsService — статистика платформы
- UserService, PaymentService, BalanceService и др.
"""

from .health_service import HealthService
from .stats_service import StatsService
from .user_service import UserService
from .payment_service import PaymentService
from .balance_service import BalanceService
from .order_service import OrderService
from .task_service import TaskService
from .referral_service import ReferralService

__all__ = [
    "HealthService",
    "StatsService",
    "UserService",
    "PaymentService",
    "BalanceService",
    "OrderService",
    "TaskService",
    "ReferralService",
]
