"""
Uzinex Boost — Domain Services
==============================

Сервисный слой бизнес-логики платформы Uzinex Boost v2.0.

Назначение:
-----------
Содержит основные бизнес-сервисы, которые объединяют:
- репозитории данных (db.repositories),
- доменные правила (domain.rules),
- события (domain.events).

Каждый сервис отвечает за конкретный аспект платформы:
-------------------------------------------------------
• UserService       — управление пользователями, профилем и статусом.
• BalanceService    — операции с балансом, начисления и списания.
• PaymentService    — работа с внешними и внутренними платежами.
• OrderService      — управление заказами, подтверждения и завершения.
• TaskService       — задания, выполнение и вознаграждение.
• ReferralService   — бонусы и уровни реферальной программы.

Принципы:
----------
1. Асинхронное исполнение.
2. Правила → проверка условий (`domain.rules`).
3. Репозитории → изменение состояния (`db.repositories`).
4. События → реакция и интеграция (`domain.events`).
5. Чистая архитектура: логика изолирована от API и ORM.

Пример использования:
---------------------
from domain.services import BalanceService

service = BalanceService(session)
await service.withdraw(user_id=1, amount=50000)
"""

from domain.services.base import BaseService
from domain.services.user_service import UserService
from domain.services.balance_service import BalanceService
from domain.services.payment_service import PaymentService
from domain.services.order_service import OrderService
from domain.services.task_service import TaskService
from domain.services.referral_service import ReferralService

__all__ = [
    # Базовый слой
    "BaseService",

    # Конкретные сервисы
    "UserService",
    "BalanceService",
    "PaymentService",
    "OrderService",
    "TaskService",
    "ReferralService",
]
