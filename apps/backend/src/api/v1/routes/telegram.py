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

from adapters.telegram.webhook import telegram_webhook
from api.v1.deps import get_bot_service
from bot.app.service import BotService, NotificationDeliveryError, WebAppAuthError

logger = logging.getLogger("uzinex.api.telegram")

router = APIRouter(tags=["Telegram"], prefix="/telegram")


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
    bot_service: BotService = Depends(get_bot_service),
):
    """
    🔐 Проверяет подлинность initData и возвращает токен авторизации (UZT-session).
    """
    try:
        auth_result = await bot_service.authenticate_webapp(init_data=init_data, bot_token=bot_token)
        logger.info(
            "[Telegram] WebApp auth OK for telegram_id=%s",
            auth_result.user.telegram_id,
        )
        return auth_result.to_dict()
    except WebAppAuthError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - defensive branch
        logger.exception("[Telegram] WebApp auth failed")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


# -------------------------------------------------
# 🔹 Тестовое уведомление (для отладки)
# -------------------------------------------------

@router.post("/notify", response_model=Dict[str, Any])
async def send_test_notification(
    bot_service: BotService = Depends(get_bot_service),
    user_id: int = Query(..., description="Telegram ID получателя"),
    text: str = Query(..., description="Текст уведомления"),
):
    """
    🧪 Отправляет тестовое уведомление пользователю через Telegram.
    Используется для проверки интеграции Bot API.
    """
    try:
        result = await bot_service.notify_user(user_id=user_id, text=text, message_type="info")
        logger.info("[Telegram] Test notification sent to %s", user_id)
        return {"ok": result.delivered, "message": "Notification sent"}
    except NotificationDeliveryError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - defensive branch
        logger.exception("[Telegram] Failed to send test notification")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))
