"""
Uzinex Boost API v1 — Schemas Package
=====================================

Пакет Pydantic-схем, описывающих структуры данных,
используемые во всех REST-эндпоинтах Boost v2.0.

Назначение:
- валидация входных и выходных данных;
- строгая типизация API;
- документация (Swagger, ReDoc);
- сериализация domain-моделей.

Подразделы:
    base.py              — общие базовые модели и миксины
    user_schemas.py      — модели пользователей
    balance_schemas.py   — баланс и транзакции
    order_schemas.py     — заказы и продвижения
    task_schemas.py      — задания (earn)
    payment_schemas.py   — пополнения / чек-система
    telegram_schemas.py  — Telegram WebApp / webhook
    system_schemas.py    — служебные схемы (ping, health, version)
    stats_schemas.py     — статистика и аналитика
"""

from .base import BaseResponse, ErrorResponse, TimestampMixin, IDMixin
from .user_schemas import (
    UserRead,
    UserUpdate,
    UserProfileResponse,
    UserReferralsResponse,
)
from .balance_schemas import BalanceResponse, TransactionRecord
from .order_schemas import OrderCreate, OrderResponse, OrderStatsResponse
from .task_schemas import TaskRead, TaskCompleteResponse, TaskStatsResponse
from .payment_schemas import (
    PaymentCreateRequest,
    PaymentStatusResponse,
    PaymentHistoryRecord,
)
from .telegram_schemas import (
    WebAppAuthRequest,
    WebAppAuthResponse,
    NotificationRequest,
)
from .system_schemas import PingResponse, VersionResponse, HealthResponse
from .stats_schemas import UserStatsResponse, SystemStatsResponse


__all__ = [
    # Base
    "BaseResponse",
    "ErrorResponse",
    "TimestampMixin",
    "IDMixin",

    # Users
    "UserRead",
    "UserUpdate",
    "UserProfileResponse",
    "UserReferralsResponse",

    # Balance
    "BalanceResponse",
    "TransactionRecord",

    # Orders
    "OrderCreate",
    "OrderResponse",
    "OrderStatsResponse",

    # Tasks
    "TaskRead",
    "TaskCompleteResponse",
    "TaskStatsResponse",

    # Payments
    "PaymentCreateRequest",
    "PaymentStatusResponse",
    "PaymentHistoryRecord",

    # Telegram
    "WebAppAuthRequest",
    "WebAppAuthResponse",
    "NotificationRequest",

    # System
    "PingResponse",
    "VersionResponse",
    "HealthResponse",

    # Stats
    "UserStatsResponse",
    "SystemStatsResponse",
]
