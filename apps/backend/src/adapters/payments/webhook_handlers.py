"""
Uzinex Boost — Payment Webhook Handlers
=======================================

Модуль обработки входящих callback/webhook уведомлений от платёжных провайдеров.

Задачи:
- принять и разобрать HTTP-запрос от провайдера,
- определить тип провайдера (click, payme, apelsin и т.д.),
- проверить подпись и целостность данных,
- нормализовать payload в единый формат для сервиса платежей.

Все провайдеры должны реализовать метод `parse_callback()` в своём адаптере.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from fastapi import Request

from . import get_provider
from .exceptions import InvalidSignature, WebhookAuthError, PaymentError


logger = logging.getLogger("uzinex.payments.webhook")


# ----------------------------
# 🔹 Основная точка входа
# ----------------------------

async def handle_webhook(request: Request, provider_name: str) -> Dict[str, Any]:
    """
    Принимает webhook от провайдера и возвращает нормализованный payload.

    :param request: FastAPI Request объект
    :param provider_name: имя провайдера ("click", "payme", "apelsin" и т.д.)
    :return: dict вида:
        {
            "invoice_id": str,
            "status": str,
            "amount_uzt": float,
            "signature_valid": bool,
            "raw": dict
        }
    """
    try:
        # Определяем провайдера
        provider = get_provider(provider_name)

        # Извлекаем данные из запроса
        headers = dict(request.headers)
        content_type = headers.get("content-type", "").lower()
        if "application/json" in content_type:
            data = await request.json()
        else:
            form = await request.form()
            data = dict(form)

        logger.info(f"[Webhook] Received from {provider_name}: {data}")

        # Парсим и валидация подписи через адаптер
        parsed = await provider.parse_callback(data, headers)

        # Проверяем подпись
        if not parsed.get("signature_valid", False):
            logger.warning(f"[Webhook] Invalid signature from {provider_name}: {data}")
            raise InvalidSignature(f"Invalid signature from {provider_name}")

        normalized = {
            "invoice_id": parsed.get("invoice_id"),
            "status": parsed.get("status"),
            "amount_uzt": parsed.get("amount_uzt", 0),
            "signature_valid": True,
            "provider": provider_name,
            "raw": data,
        }

        logger.info(f"[Webhook] Validated callback from {provider_name}: {normalized}")
        return normalized

    except InvalidSignature as e:
        raise WebhookAuthError(str(e)) from e

    except Exception as e:
        logger.exception(f"[Webhook] Error handling callback from {provider_name}: {e}")
        raise PaymentError(f"Webhook processing failed: {e}") from e


# ----------------------------
# 🔹 Хелпер для FastAPI маршрута
# ----------------------------

async def webhook_entrypoint(request: Request, provider_name: str) -> Dict[str, Any]:
    """
    Универсальная обёртка для использования в FastAPI router.
    Можно подключить как:
        @router.post("/webhook/{provider_name}")
        async def payment_webhook(provider_name: str, request: Request):
            return await webhook_entrypoint(request, provider_name)
    """
    result = await handle_webhook(request, provider_name)
    return {"ok": True, "provider": provider_name, "data": result}
