"""
Uzinex Boost — Task Events
==========================

События, связанные с заданиями (tasks) и их жизненным циклом.

Назначение:
-----------
- описывают все ключевые этапы работы с заданиями;
- позволяют сервисам реагировать на выполнение, проверку и награждение;
- используются для аналитики, уведомлений и начисления UZT.

Используется в:
---------------
- domain.services.task
- domain.services.balance
- adapters.analytics
- adapters.notifications
"""

from __future__ import annotations
from datetime import datetime
from pydantic import Field

from domain.events.base import DomainEvent


# -------------------------------------------------
# 🔹 Событие: Задание создано
# -------------------------------------------------
class TaskCreatedEvent(DomainEvent):
    """Генерируется при создании нового задания пользователем или системой."""

    event_type: str = "task.created"
    task_id: int = Field(..., description="ID задания")
    creator_id: int = Field(..., description="ID пользователя, создавшего задание")
    title: str = Field(..., description="Название задания")
    reward: float = Field(..., description="Вознаграждение за выполнение (UZT)")
    created_at: datetime = Field(default_factory=datetime.utcnow)


# -------------------------------------------------
# 🔹 Событие: Задание принято исполнителем (новое)
# -------------------------------------------------
class TaskAcceptedEvent(DomainEvent):
    """Генерируется, когда исполнитель принимает задание и начинает его выполнение."""

    event_type: str = "task.accepted"
    task_id: int
    user_id: int = Field(..., description="ID исполнителя, принявшего задание")
    accepted_at: datetime = Field(default_factory=datetime.utcnow)


# -------------------------------------------------
# 🔹 Событие: Задание взято в работу
# -------------------------------------------------
class TaskAssignedEvent(DomainEvent):
    """Генерируется, когда система назначает задание конкретному исполнителю."""

    event_type: str = "task.assigned"
    task_id: int
    user_id: int = Field(..., description="ID исполнителя")
    assigned_at: datetime = Field(default_factory=datetime.utcnow)


# -------------------------------------------------
# 🔹 Событие: Задание выполнено
# -------------------------------------------------
class TaskCompletedEvent(DomainEvent):
    """Генерируется, когда пользователь успешно завершает задание."""

    event_type: str = "task.completed"
    task_id: int
    user_id: int
    reward: float = Field(..., description="Вознаграждение за выполнение")
    verified: bool = Field(default=False, description="Подтверждено ли модератором")
    completed_at: datetime = Field(default_factory=datetime.utcnow)


# -------------------------------------------------
# 🔹 Событие: Задание проверено и одобрено
# -------------------------------------------------
class TaskApprovedEvent(DomainEvent):
    """Генерируется, когда модератор одобрил выполненное задание."""

    event_type: str = "task.approved"
    task_id: int
    user_id: int
    reward: float
    approved_by: int = Field(..., description="ID модератора, одобрившего задание")
    approved_at: datetime = Field(default_factory=datetime.utcnow)


# -------------------------------------------------
# 🔹 Событие: Задание отклонено (ошибка/мошенничество)
# -------------------------------------------------
class TaskRejectedEvent(DomainEvent):
    """Генерируется, когда задание отклонено модератором."""

    event_type: str = "task.rejected"
    task_id: int
    user_id: int
    reason: str = Field(..., description="Причина отклонения задания")
    rejected_by: int = Field(..., description="ID модератора, отклонившего задание")
    rejected_at: datetime = Field(default_factory=datetime.utcnow)


# -------------------------------------------------
# 🔹 Событие: Вознаграждение за задание начислено
# -------------------------------------------------
class TaskRewardedEvent(DomainEvent):
    """Генерируется, когда пользователю начисляется вознаграждение за выполненное задание."""

    event_type: str = "task.rewarded"
    task_id: int
    user_id: int
    reward: float
    balance_before: float
    balance_after: float
    transaction_id: int | None = Field(None, description="ID транзакции начисления")
    rewarded_at: datetime = Field(default_factory=datetime.utcnow)
