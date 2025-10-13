"""
Uzinex Boost API v1 — Telegram Routes
=====================================

Эндпоинты для интеграции Telegram Bot и WebApp:
- /webhook — приём обновлений от Telegram Bot API;
- /auth/webapp — проверка и авторизация пользователей через initData;
- /notify — служебная отправка уведомлений пользователям (для тестов и админов).

Интеграция:
использует adapters.telegram (client, webapp_auth, notifier)
"""

from __future__ import annotations

import logging
from typing import Any, Dict

from fastapi import APIRouter, Request, Depends, HTTPException, status, Query

from adapters.telegram import (
    TelegramClient,
    validate_webapp_data,
    send_notification,
)
from adapters.telegram.webhook import telegram_webhook
from core.security import create_user_session  # создаёт JWT/UZT-токен для WebApp
from domain.services.users import UserService

logger = logging.getLogger("uzinex.api.telegram")

router = APIRouter(tags=["Telegram"], prefix="/telegram")


# -------------------------------------------------
# 🔹 Зависимости
# -------------------------------------------------

async def get_user_service() -> UserService:
    return UserService()


# -------------------------------------------------
# 🔹 Webhook endpoint (бот)
# -------------------------------------------------

@router.post("/webhook")
async def telegram_bot_webhook(request: Request):
    """
    🤖 Принимает webhook-запросы от Telegram Bot API.
    """
    return await telegram_webhook(request)


# -------------------------------------------------
# 🔹 Авторизация через Telegram WebApp
# -------------------------------------------------

@router.post("/auth/webapp", response_model=Dict[str, Any])
async def telegram_webapp_auth(
    init_data: str = Query(..., description="Telegram WebApp initData строка"),
    bot_token: str = Query(..., description="Токен Telegram-бота"),
    user_service: UserService = Depends(get_user_service),
):
    """
    🔐 Проверяет подлинность initData и возвращает токен авторизации (UZT-session).
    """
    try:
        validation = validate_webapp_data(init_data, bot_token)
        if not validation.valid:
            raise HTTPException(status_code=400, detail="Invalid Telegram data")

        # Проверяем наличие пользователя в базе
        user = await user_service.get_or_create_telegram_user(
            telegram_id=validation.user_id,
            username=validation.username,
        )

        # Создаём JWT/UZT session-токен
        token = create_user_session(user)

        logger.info(f"[Telegram] WebApp auth OK for {validation.username} (ID={validation.user_id})")
        return {
            "ok": True,
            "user": {
                "id": user.id,
                "username": user.username,
                "balance": user.balance_uzt,
            },
            "session_token": token,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("[Telegram] WebApp auth failed")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# -------------------------------------------------
# 🔹 Тестовое уведомление (для отладки)
# -------------------------------------------------

@router.post("/notify", response_model=Dict[str, Any])
async def send_test_notification(
    telegram_client: TelegramClient = Depends(),
    user_id: int = Query(..., description="Telegram ID получателя"),
    text: str = Query(..., description="Текст уведомления"),
):
    """
    🧪 Отправляет тестовое уведомление пользователю через Telegram.
    Используется для проверки интеграции Bot API.
    """
    try:
        await send_notification(telegram_client, user_id=user_id, text=text, message_type="info")
        logger.info(f"[Telegram] Test notification sent to {user_id}")
        return {"ok": True, "message": "Notification sent"}
    except Exception as e:
        logger.exception("[Telegram] Failed to send test notification")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
