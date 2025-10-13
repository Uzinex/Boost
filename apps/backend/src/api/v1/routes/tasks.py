"""
Uzinex Boost API v1 — Tasks Routes
===================================

Эндпоинты для заработка пользователей:
- получение списка активных заданий;
- выполнение задания (с проверкой);
- получение истории выполненных задач;
- получение статистики по заработку.

Интеграция:
использует domain.services.tasks, balance и telegram для уведомлений.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, status, Query

from domain.services.tasks import TaskService
from domain.services.balance import BalanceService
from adapters.telegram import TelegramClient, send_notification
from core.security import get_current_user  # авторизация через Telegram WebApp

logger = logging.getLogger("uzinex.api.tasks")

router = APIRouter(tags=["Tasks"], prefix="/tasks")


# -------------------------------------------------
# 🔹 Вспомогательные зависимости
# -------------------------------------------------

async def get_task_service() -> TaskService:
    return TaskService()


async def get_balance_service() -> BalanceService:
    return BalanceService()


# -------------------------------------------------
# 🔹 Получение доступных заданий
# -------------------------------------------------

@router.get("/", response_model=List[Dict[str, Any]])
async def list_available_tasks(
    task_service: TaskService = Depends(get_task_service),
    current_user: Dict[str, Any] = Depends(get_current_user),
    limit: int = Query(20, ge=1, le=100, description="Максимум задач"),
):
    """
    📋 Возвращает список активных заданий для пользователя.
    """
    try:
        tasks = await task_service.list_available_tasks(user_id=current_user["id"], limit=limit)
        logger.info(f"[Tasks] {current_user['id']} fetched {len(tasks)} tasks")
        return tasks
    except Exception as e:
        logger.exception("[Tasks] Failed to list tasks")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# -------------------------------------------------
# 🔹 Выполнение задания
# -------------------------------------------------

@router.post("/{task_id}/complete", response_model=Dict[str, Any])
async def complete_task(
    task_id: int,
    task_service: TaskService = Depends(get_task_service),
    balance_service: BalanceService = Depends(get_balance_service),
    telegram_client: TelegramClient = Depends(),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    ✅ Отмечает задание выполненным и начисляет вознаграждение пользователю.
    """
    try:
        result = await task_service.complete_task(task_id=task_id, user_id=current_user["id"])

        if not result:
            raise HTTPException(status_code=400, detail="Невозможно выполнить это задание")

        reward = result["reward"]
        await balance_service.increase_balance(current_user["id"], reward)

        # Отправка уведомления в Telegram
        await send_notification(
            telegram_client,
            user_id=current_user["id"],
            text=f"🎉 Задание #{task_id} выполнено!\nНачислено: <b>{reward:.2f} UZT</b>",
            message_type="success",
        )

        logger.info(f"[Tasks] User {current_user['id']} completed task {task_id} (+{reward} UZT)")
        return {"ok": True, "task_id": task_id, "reward": reward}

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("[Tasks] Task completion error")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# -------------------------------------------------
# 🔹 История выполненных заданий
# -------------------------------------------------

@router.get("/history", response_model=List[Dict[str, Any]])
async def get_completed_tasks(
    task_service: TaskService = Depends(get_task_service),
    current_user: Dict[str, Any] = Depends(get_current_user),
    limit: int = Query(50, description="Количество последних записей"),
):
    """
    🧾 Возвращает историю выполненных пользователем заданий.
    """
    try:
        history = await task_service.list_completed_tasks(user_id=current_user["id"], limit=limit)
        return history
    except Exception as e:
        logger.exception("[Tasks] Failed to fetch completed tasks")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# -------------------------------------------------
# 🔹 Ежедневная статистика
# -------------------------------------------------

@router.get("/stats", response_model=Dict[str, Any])
async def get_task_stats(
    task_service: TaskService = Depends(get_task_service),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    📊 Возвращает статистику по заработку пользователя:
    - количество выполненных заданий;
    - суммарный доход;
    - средний доход за день.
    """
    try:
        stats = await task_service.get_user_stats(user_id=current_user["id"])
        logger.info(f"[Tasks] Stats fetched for user {current_user['id']}")
        return {"ok": True, "data": stats}
    except Exception as e:
        logger.exception("[Tasks] Failed to fetch task stats")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
