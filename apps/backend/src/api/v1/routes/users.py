"""
Uzinex Boost API v1 — Users Routes
===================================

Эндпоинты для работы с пользователями:
- регистрация и авторизация (через Telegram WebApp);
- получение и обновление профиля;
- реферальная информация;
- внутренняя статистика пользователя.

Интеграция:
использует domain.services.users, balance, telegram, security.
"""

from __future__ import annotations

import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status, Query

from domain.services.users import UserService
from domain.services.balance import BalanceService
from adapters.telegram import TelegramClient, send_notification
from core.security import get_current_user

logger = logging.getLogger("uzinex.api.users")

router = APIRouter(tags=["Users"], prefix="/users")


# -------------------------------------------------
# 🔹 Вспомогательные зависимости
# -------------------------------------------------

async def get_user_service() -> UserService:
    return UserService()


async def get_balance_service() -> BalanceService:
    return BalanceService()


# -------------------------------------------------
# 🔹 Получение своего профиля
# -------------------------------------------------

@router.get("/me", response_model=Dict[str, Any])
async def get_profile(
    current_user: Dict[str, Any] = Depends(get_current_user),
    balance_service: BalanceService = Depends(get_balance_service),
):
    """
    👤 Возвращает данные текущего пользователя и его баланс.
    """
    try:
        balance = await balance_service.get_balance(current_user["id"])
        return {
            "ok": True,
            "user": {
                "id": current_user["id"],
                "username": current_user.get("username"),
                "first_name": current_user.get("first_name"),
                "language": current_user.get("language", "ru"),
                "balance": balance,
            },
        }
    except Exception as e:
        logger.exception("[Users] Failed to fetch profile")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# -------------------------------------------------
# 🔹 Обновление профиля
# -------------------------------------------------

@router.post("/update", response_model=Dict[str, Any])
async def update_profile(
    username: str | None = Query(None, description="Никнейм Telegram или имя пользователя"),
    language: str | None = Query(None, description="Предпочитаемый язык интерфейса"),
    user_service: UserService = Depends(get_user_service),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    ✏️ Обновляет профиль пользователя.
    """
    try:
        updated = await user_service.update_user(
            user_id=current_user["id"],
            username=username,
            language=language,
        )
        logger.info(f"[Users] Updated profile for user {current_user['id']}")
        return {"ok": True, "user": updated}
    except Exception as e:
        logger.exception("[Users] Failed to update profile")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# -------------------------------------------------
# 🔹 Реферальная информация
# -------------------------------------------------

@router.get("/referrals", response_model=Dict[str, Any])
async def get_referrals(
    user_service: UserService = Depends(get_user_service),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    🤝 Возвращает список рефералов пользователя.
    """
    try:
        referrals = await user_service.get_referrals(current_user["id"])
        return {"ok": True, "count": len(referrals), "referrals": referrals}
    except Exception as e:
        logger.exception("[Users] Failed to fetch referrals")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# -------------------------------------------------
# 🔹 Уведомление (вручную для тестов)
# -------------------------------------------------

@router.post("/notify", response_model=Dict[str, Any])
async def user_notify(
    telegram_client: TelegramClient = Depends(),
    text: str = Query(..., description="Текст уведомления"),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    📩 Отправляет уведомление пользователю (тестовое).
    """
    try:
        await send_notification(
            telegram_client,
            user_id=current_user["id"],
            text=text,
            message_type="info",
        )
        logger.info(f"[Users] Notification sent to user {current_user['id']}")
        return {"ok": True, "message": "Notification sent"}
    except Exception as e:
        logger.exception("[Users] Failed to send notification")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# -------------------------------------------------
# 🔹 Удаление аккаунта
# -------------------------------------------------

@router.delete("/delete", response_model=Dict[str, Any])
async def delete_account(
    user_service: UserService = Depends(get_user_service),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    ⚠️ Удаляет аккаунт пользователя (по запросу).
    """
    try:
        await user_service.delete_user(current_user["id"])
        logger.warning(f"[Users] User {current_user['id']} deleted their account")
        return {"ok": True, "message": "Account deleted"}
    except Exception as e:
        logger.exception("[Users] Failed to delete account")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
