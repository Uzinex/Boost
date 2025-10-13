"""
Uzinex Boost — Telegram Webhook Handler
=======================================

Модуль для приёма и проверки webhook-запросов от Telegram Bot API.

Назначение:
- безопасная обработка POST-запросов от Telegram;
- валидация update-структуры;
- интеграция с FastAPI (через router или напрямую);
- централизованное логирование и обработка ошибок.

Webhook используется, если бот запущен не через polling.
"""

from __future__ import annotations

import logging
from typing import Any, Dict

from fastapi import APIRouter, Request, HTTPException, status

from .exceptions import WebhookUnauthorized, WebhookProcessingError
from .types import TelegramMessage, TelegramCallback
from .utils import log_event


logger = logging.getLogger("uzinex.telegram.webhook")

router = APIRouter(prefix="/telegram", tags=["Telegram Webhook"])


# ----------------------------
# 🔹 Вспомогательная функция
# ----------------------------

async def _parse_update(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Определяет тип обновления (message / callback_query)
    и возвращает нормализованную структуру.
    """
    if "message" in data:
        message = data["message"]
        parsed = {
            "update_type": "message",
            "user_id": message["from"]["id"],
            "text": message.get("text"),
        }
        return parsed

    if "callback_query" in data:
        callback = data["callback_query"]
        parsed = {
            "update_type": "callback",
            "user_id": callback["from"]["id"],
            "data": callback.get("data"),
        }
        return parsed

    return {"update_type": "unknown", "raw": data}


# ----------------------------
# 🔹 Основной webhook endpoint
# ----------------------------

@router.post("/webhook")
async def telegram_webhook(request: Request) -> Dict[str, Any]:
    """
    Главный endpoint для Telegram Webhook.

    Пример: POST /telegram/webhook
    """
    try:
        body = await request.json()
        logger.info(f"[Webhook] Incoming update: {body}")

        update = await _parse_update(body)
        log_event(f"Received {update['update_type']} from user {update.get('user_id')}", level="info")

        # Здесь можно добавить вызов бизнес-логики, например:
        # await process_telegram_event(update)

        return {"ok": True, "status": "processed", "update_type": update["update_type"]}

    except WebhookUnauthorized as e:
        logger.warning(f"[Webhook] Unauthorized request: {e}")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized webhook")

    except Exception as e:
        logger.exception(f"[Webhook] Processing error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Webhook processing failed")


# ----------------------------
# 🔹 Проверка валидности (для будущего)
# ----------------------------

async def verify_webhook_source(request: Request, secret_token: str | None = None) -> None:
    """
    Проверяет источник запроса (по X-Telegram-Bot-Api-Secret-Token, если задан).
    Telegram добавляет этот заголовок при вызове webhook.
    """
    if not secret_token:
        return  # не используется, если токен не задан

    header_token = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
    if header_token != secret_token:
        logger.warning("[Webhook] Invalid secret token")
        raise WebhookUnauthorized("Invalid webhook secret token")
