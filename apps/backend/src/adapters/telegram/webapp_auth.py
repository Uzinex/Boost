"""
Uzinex Boost — Telegram WebApp Auth Validator
=============================================

Модуль для проверки подлинности данных Telegram WebApp (initData).

Назначение:
- проверка подписи hash с помощью HMAC SHA256 (bot_token);
- проверка срока действия auth_date;
- возврат безопасных данных пользователя для авторизации.

Документация:
https://core.telegram.org/bots/webapps#validating-data-received-via-the-web-app
"""

from __future__ import annotations

import hmac
import hashlib
import logging
import urllib.parse
from datetime import datetime, timezone, timedelta
from typing import Dict, Any

from .types import WebAppData, WebAppValidationResult
from .exceptions import InvalidInitData, ExpiredInitData


logger = logging.getLogger("uzinex.telegram.webapp_auth")


# ----------------------------
# 🔹 Основная функция проверки
# ----------------------------

def validate_webapp_data(init_data: str, bot_token: str, max_age_seconds: int = 86400) -> WebAppValidationResult:
    """
    Проверяет initData, переданную из Telegram WebApp.

    :param init_data: строка initData, полученная из window.Telegram.WebApp.initData
    :param bot_token: токен Telegram-бота
    :param max_age_seconds: допустимый срок действия auth_date (по умолчанию 24 часа)
    :return: WebAppValidationResult
    """
    if not init_data:
        logger.warning("[WebAppAuth] initData is empty")
        raise InvalidInitData("Missing initData")

    # Парсим initData в dict
    parsed_data = dict(urllib.parse.parse_qsl(init_data, strict_parsing=True))
    user_data = parsed_data.get("user")
    auth_date = parsed_data.get("auth_date")
    received_hash = parsed_data.get("hash")

    if not all([user_data, auth_date, received_hash]):
        raise InvalidInitData("initData missing required fields")

    # Собираем строку для HMAC-проверки
    check_pairs = [f"{k}={v}" for k, v in sorted(parsed_data.items()) if k != "hash"]
    data_check_string = "\n".join(check_pairs)

    # Формируем секретный ключ
    secret_key = hashlib.sha256(bot_token.encode()).digest()

    # Вычисляем ожидаемую подпись
    expected_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    # Сравнение подписи
    if not hmac.compare_digest(expected_hash, received_hash):
        logger.warning("[WebAppAuth] Invalid HMAC signature")
        raise InvalidInitData("Invalid signature in initData")

    # Проверка срока действия
    try:
        auth_timestamp = int(auth_date)
    except ValueError:
        raise InvalidInitData("Invalid auth_date format")

    now = int(datetime.now(timezone.utc).timestamp())
    if now - auth_timestamp > max_age_seconds:
        logger.warning("[WebAppAuth] initData expired")
        raise ExpiredInitData("initData expired")

    # Если всё хорошо — создаём результат
    result = WebAppValidationResult(
        valid=True,
        user_id=_extract_user_id(user_data),
        username=_extract_username(user_data),
        auth_datetime=datetime.fromtimestamp(auth_timestamp, tz=timezone.utc),
    )

    logger.info(f"[WebAppAuth] ✅ Valid initData for user {result.user_id}")
    return result


# ----------------------------
# 🔹 Вспомогательные функции
# ----------------------------

def _extract_user_id(user_json: str) -> int:
    """Извлекает user.id из JSON-строки."""
    import json
    try:
        user = json.loads(user_json)
        return int(user.get("id"))
    except Exception as e:
        logger.error(f"[WebAppAuth] Failed to extract user_id: {e}")
        raise InvalidInitData("Invalid user JSON format")


def _extract_username(user_json: str) -> str | None:
    """Извлекает username из JSON-строки."""
    import json
    try:
        user = json.loads(user_json)
        return user.get("username")
    except Exception:
        return None
