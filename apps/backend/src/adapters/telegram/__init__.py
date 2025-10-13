"""
Uzinex Boost — Telegram Integration Adapter
===========================================

Инфраструктурный модуль для взаимодействия backend-системы с Telegram API.

Назначение:
- проверка и авторизация Telegram WebApp (initData);
- отправка уведомлений пользователям и администраторам;
- обработка webhook-запросов от Telegram (если используется режим webhook);
- централизованная работа с Telegram Bot API.

Основной интерфейс:
    - TelegramClient — низкоуровневый клиент для запросов к Telegram Bot API
    - validate_webapp_data() — проверка подлинности initData
    - send_notification() — отправка уведомлений пользователям
"""

from .client import TelegramClient
from .webapp_auth import validate_webapp_data
from .notifier import send_notification
from .exceptions import (
    TelegramAPIError,
    InvalidInitData,
    WebhookUnauthorized,
)
from . import utils

__all__ = [
    "TelegramClient",
    "validate_webapp_data",
    "send_notification",
    "TelegramAPIError",
    "InvalidInitData",
    "WebhookUnauthorized",
    "utils",
]
