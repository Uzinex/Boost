"""
Uzinex Boost API v1 — Task Schemas
===================================

Схемы данных, связанные с системой заданий (earn-механика):
- получение списка доступных заданий;
- выполнение задания;
- статистика заработка пользователя;
- интеграция с балансом и системой вознаграждений.
"""

from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional

from .base import IDMixin, TimestampMixin


# -------------------------------------------------
# 🔹 Модель задачи (для отображения пользователю)
# -------------------------------------------------

class TaskRead(IDMixin, TimestampMixin):
    """Детальная информация о задании, доступном пользователю."""

    order_id: int = Field(..., description="ID связанного заказа (promotion source)")
    title: str = Field(..., description="Краткое описание задания")
    task_type: str = Field(..., description="Тип задания: 'channel' | 'group' | 'view'")
    target_url: str = Field(..., description="Ссылка на выполнение задания")
    reward: float = Field(..., ge=0.1, description="Награда за выполнение (в UZT)")
    is_completed: bool = Field(False, description="Статус выполнения пользователем")

    class Config:
        orm_mode = True
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 302,
                "order_id": 120,
                "title": "Подпишитесь на @uzinex",
                "task_type": "channel",
                "target_url": "https://t.me/uzinex",
                "reward": 0.6,
                "is_completed": False,
                "created_at": "2025-10-12T10:30:00",
                "updated_at": "2025-10-12T10:30:00"
            }
        }


# -------------------------------------------------
# 🔹 Ответ о выполнении задания
# -------------------------------------------------

class TaskCompleteResponse(BaseModel):
    """Ответ API при успешном выполнении задания."""

    ok: bool = Field(True, description="Флаг успешности операции")
    task_id: int = Field(..., description="ID выполненного задания")
    reward: float = Field(..., ge=0, description="Начисленная награда (UZT)")
    new_balance: Optional[float] = Field(None, description="Обновлённый баланс пользователя")

    class Config:
        json_schema_extra = {
            "example": {
                "ok": True,
                "task_id": 302,
                "reward": 0.6,
                "new_balance": 125.4
            }
        }


# -------------------------------------------------
# 🔹 Статистика по задачам (для профиля)
# -------------------------------------------------

class TaskStatsResponse(BaseModel):
    """Сводная статистика по заданиям и заработку."""

    total_tasks: int = Field(..., description="Всего доступных заданий")
    completed_tasks: int = Field(..., description="Выполнено пользователем")
    total_earned_uzt: float = Field(..., description="Всего заработано в UZT")
    average_reward: float = Field(..., description="Средняя награда за задание")
    completion_rate: float = Field(..., description="Процент выполнения (0–100%)")
    last_activity: Optional[datetime] = Field(None, description="Последнее выполнение задания")

    class Config:
        json_schema_extra = {
            "example": {
                "total_tasks": 150,
                "completed_tasks": 120,
                "total_earned_uzt": 72.0,
                "average_reward": 0.6,
                "completion_rate": 80.0,
                "last_activity": "2025-10-12T19:10:00"
            }
        }
