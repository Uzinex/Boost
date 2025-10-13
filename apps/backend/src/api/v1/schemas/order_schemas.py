"""
Uzinex Boost API v1 — Order Schemas
===================================

Схемы данных, связанные с заказами (продвижениями каналов и групп).

Назначение:
- создание заказов (OrderCreate);
- отображение активных и завершённых заказов (OrderResponse);
- агрегированные данные по заказам (OrderStatsResponse);
- единая структура для WebApp и админ-панели.
"""

from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional

from .base import IDMixin, TimestampMixin


# -------------------------------------------------
# 🔹 Создание заказа
# -------------------------------------------------

class OrderCreate(BaseModel):
    """Запрос на создание нового заказа продвижения."""

    order_type: str = Field(..., description="Тип заказа: 'channel' | 'group'")
    target_url: str = Field(..., description="Ссылка на Telegram-канал или группу")
    quantity: int = Field(..., ge=10, le=10000, description="Количество участников / подписчиков")
    cost_per_action: float = Field(..., ge=0.1, description="Цена за действие (UZT)")
    total_cost: float = Field(..., ge=1, description="Общая сумма заказа (UZT)")

    class Config:
        schema_extra = {
            "example": {
                "order_type": "channel",
                "target_url": "https://t.me/uzinex",
                "quantity": 500,
                "cost_per_action": 0.6,
                "total_cost": 300.0,
            }
        }


# -------------------------------------------------
# 🔹 Ответ о заказе
# -------------------------------------------------

class OrderResponse(IDMixin, TimestampMixin):
    """Подробная информация о заказе."""

    user_id: int = Field(..., description="ID пользователя, создавшего заказ")
    order_type: str = Field(..., description="Тип заказа: channel | group")
    target_url: str = Field(..., description="Цель продвижения (ссылка)")
    quantity: int = Field(..., description="Общее количество участников / подписчиков")
    completed: int = Field(0, description="Количество выполненных действий")
    remaining: int = Field(..., description="Оставшееся количество действий")
    cost_per_action: float = Field(..., description="Стоимость одного действия (UZT)")
    total_cost: float = Field(..., description="Общая стоимость заказа (UZT)")
    status: str = Field(..., description="Статус заказа: active | paused | completed | canceled")

    class Config:
        orm_mode = True
        from_attributes = True
        schema_extra = {
            "example": {
                "id": 101,
                "user_id": 12,
                "order_type": "channel",
                "target_url": "https://t.me/uzinex",
                "quantity": 500,
                "completed": 120,
                "remaining": 380,
                "cost_per_action": 0.6,
                "total_cost": 300.0,
                "status": "active",
                "created_at": "2025-10-12T14:10:00",
                "updated_at": "2025-10-12T15:30:00",
            }
        }


# -------------------------------------------------
# 🔹 Статистика заказов (агрегированные данные)
# -------------------------------------------------

class OrderStatsResponse(BaseModel):
    """Агрегированные данные по заказам пользователя."""

    total_orders: int = Field(..., description="Общее количество заказов пользователя")
    active_orders: int = Field(..., description="Активные заказы")
    completed_orders: int = Field(..., description="Завершённые заказы")
    canceled_orders: int = Field(..., description="Отменённые заказы")
    total_spent_uzt: float = Field(..., description="Всего потрачено UZT")
    total_actions_done: int = Field(..., description="Общее количество выполненных действий")

    class Config:
        json_schema_extra = {
            "example": {
                "total_orders": 18,
                "active_orders": 4,
                "completed_orders": 12,
                "canceled_orders": 2,
                "total_spent_uzt": 3240.5,
                "total_actions_done": 1920
            }
        }
