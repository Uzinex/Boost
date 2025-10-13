"""
Uzinex Boost API v1 — Statistics Routes
=======================================

Эндпоинты для получения аналитики и статистики Boost.

Функционал:
- публичная статистика для WebApp;
- пользовательская статистика (заработок, выполненные задания);
- системная статистика для админов (через зависимость);
"""

from __future__ import annotations

import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status

from domain.services.stats import StatsService
from domain.services.task_service import TaskService
from domain.services.payment_service import PaymentService
from core.security import get_current_user, get_current_admin  # доступы

logger = logging.getLogger("uzinex.api.stats")

router = APIRouter(tags=["Statistics"], prefix="/stats")


# ----------------------------
# 🔹 Вспомогательные зависимости
# ----------------------------

async def get_stats_service() -> StatsService:
    return StatsService()


async def get_task_service() -> TaskService:
    return TaskService()


async def get_payment_service() -> PaymentService:
    return PaymentService()


# ----------------------------
# 🔹 Публичная статистика (WebApp / Landing)
# ----------------------------

@router.get("/public", response_model=Dict[str, Any])
async def get_public_stats(
    stats_service: StatsService = Depends(get_stats_service),
):
    """
    🌍 Возвращает публичную статистику (для WebApp).
    """
    try:
        stats = await stats_service.get_public_summary()
        return {
            "ok": True,
            "data": stats,
        }
    except Exception as e:
        logger.exception("[Stats] Failed to get public stats")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# ----------------------------
# 🔹 Пользовательская статистика (личный кабинет)
# ----------------------------

@router.get("/user", response_model=Dict[str, Any])
async def get_user_stats(
    current_user: Dict[str, Any] = Depends(get_current_user),
    task_service: TaskService = Depends(get_task_service),
    payment_service: PaymentService = Depends(get_payment_service),
):
    """
    👤 Возвращает статистику пользователя:
    - заработано всего;
    - количество выполненных заданий;
    - активные заказы и операции.
    """
    try:
        total_earned = await task_service.get_total_earned(user_id=current_user["id"])
        completed_tasks = await task_service.count_completed(user_id=current_user["id"])
        total_deposits = await payment_service.get_total_paid(user_id=current_user["id"])

        return {
            "ok": True,
            "data": {
                "total_earned_uzt": total_earned,
                "tasks_completed": completed_tasks,
                "total_deposit_uzt": total_deposits,
            },
        }
    except Exception as e:
        logger.exception(f"[Stats] Failed to get user stats for {current_user['id']}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# ----------------------------
# 🔹 Системная статистика (для админов)
# ----------------------------

@router.get("/system", response_model=Dict[str, Any])
async def get_system_stats(
    stats_service: StatsService = Depends(get_stats_service),
    current_admin: Dict[str, Any] = Depends(get_current_admin),
):
    """
    ⚙️ Возвращает расширенную статистику системы (для админов):
    - общее количество пользователей;
    - общая сумма пополнений;
    - общий оборот UZT;
    - активные заказы и выполненные задачи.
    """
    try:
        data = await stats_service.get_system_summary()
        logger.info(f"[Stats] Admin {current_admin['username']} fetched system stats.")
        return {"ok": True, "data": data}
    except Exception as e:
        logger.exception("[Stats] Failed to get system stats")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
