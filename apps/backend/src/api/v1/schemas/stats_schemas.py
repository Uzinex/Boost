"""
Uzinex Boost API v1 — Statistics Schemas
=========================================

Схемы данных для аналитики и статистики:
- пользовательская статистика (заработок, задания, пополнения);
- системная статистика (общее количество пользователей, заказов, оборот);
- агрегированные данные для WebApp и админ-панели.
"""

from __future__ import annotations
from pydantic import BaseModel, Field


# -------------------------------------------------
# 🔹 Пользовательская статистика
# -------------------------------------------------

class UserStatsResponse(BaseModel):
    """Показатели активности и заработка пользователя."""

    total_tasks_completed: int = Field(..., description="Общее количество выполненных заданий")
    total_earned_uzt: float = Field(..., description="Общий заработок в UZT")
    total_spent_uzt: float = Field(..., description="Общая сумма потраченных средств (UZT)")
    total_deposits_uzt: float = Field(..., description="Общая сумма пополнений (UZT)")
    avg_daily_income: float = Field(..., description="Средний ежедневный доход пользователя (UZT)")
    active_orders: int = Field(..., description="Количество активных заказов пользователя")

    class Config:
        json_schema_extra = {
            "example": {
                "total_tasks_completed": 154,
                "total_earned_uzt": 91.8,
                "total_spent_uzt": 250.0,
                "total_deposits_uzt": 300.0,
                "avg_daily_income": 3.06,
                "active_orders": 2
            }
        }


# -------------------------------------------------
# 🔹 Системная статистика (админ-панель / мониторинг)
# -------------------------------------------------

class SystemStatsResponse(BaseModel):
    """Глобальные показатели системы Boost (для админов и дашборда)."""

    total_users: int = Field(..., description="Всего зарегистрированных пользователей")
    total_orders: int = Field(..., description="Всего заказов в системе")
    total_tasks_completed: int = Field(..., description="Всего выполненных заданий")
    total_earned_uzt: float = Field(..., description="Всего выплачено UZT пользователям")
    total_spent_uzt: float = Field(..., description="Всего потрачено UZT на продвижение")
    total_deposited_uzt: float = Field(..., description="Всего пополнено через систему")
    average_reward_per_task: float = Field(..., description="Среднее вознаграждение за задание (UZT)")
    uptime_hours: float = Field(..., description="Время работы API (в часах)")
    version: str = Field("2.0.0", description="Версия API")

    class Config:
        json_schema_extra = {
            "example": {
                "total_users": 5843,
                "total_orders": 1520,
                "total_tasks_completed": 44120,
                "total_earned_uzt": 92040.5,
                "total_spent_uzt": 112000.0,
                "total_deposited_uzt": 105000.0,
                "average_reward_per_task": 0.52,
                "uptime_hours": 126.5,
                "version": "2.0.0"
            }
        }


# -------------------------------------------------
# 🔹 Публичная статистика (для WebApp главной страницы)
# -------------------------------------------------

class PublicStatsResponse(BaseModel):
    """Сокращённая публичная статистика (для отображения в WebApp)."""

    total_users: int = Field(..., description="Количество пользователей Boost")
    total_earned_uzt: float = Field(..., description="Суммарно выплачено пользователям (UZT)")
    total_orders: int = Field(..., description="Всего активных и завершённых заказов")

    class Config:
        json_schema_extra = {
            "example": {
                "total_users": 5843,
                "total_earned_uzt": 92040.5,
                "total_orders": 1520
            }
        }
