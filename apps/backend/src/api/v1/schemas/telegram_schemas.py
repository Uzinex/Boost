"""
Uzinex Boost API v1 — Telegram Schemas
=======================================

Схемы данных для Telegram-интеграции:
- авторизация через WebApp (initData);
- webhook-события (callback, message);
- уведомления пользователям.

Используется в адаптерах и API-эндпоинтах `/telegram/*`.
"""

from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional


# -------------------------------------------------
# 🔹 Авторизация через Telegram WebApp
# -------------------------------------------------

class WebAppAuthRequest(BaseModel):
    """Запрос на авторизацию через Telegram WebApp initData."""

    init_data: str = Field(..., description="Строка initData, переданная Telegram WebApp")
    referrer_id: Optional[int] = Field(None, description="ID рефера, если пользователь приглашён")
    platform: Optional[str] = Field("webapp", description="Источник авторизации (webapp, bot, api)")

    class Config:
        json_schema_extra = {
            "example": {
                "init_data": "query_id=AAE123xyz&user={...}&hash=abc123",
                "referrer_id": 42,
                "platform": "webapp"
            }
        }


class WebAppAuthResponse(BaseModel):
    """Ответ после успешной авторизации пользователя через Telegram WebApp."""

    ok: bool = Field(True, description="Статус авторизации")
    user_id: int = Field(..., description="ID пользователя в системе Boost")
    username: Optional[str] = Field(None, description="Telegram username")
    first_name: Optional[str] = Field(None, description="Имя пользователя")
    session_token: str = Field(..., description="Временный JWT-токен для API")
    is_new: bool = Field(False, description="Флаг: новый пользователь или уже существующий")

    class Config:
        json_schema_extra = {
            "example": {
                "ok": True,
                "user_id": 1201,
                "username": "feruz",
                "first_name": "Feruz",
                "session_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "is_new": True
            }
        }


# -------------------------------------------------
# 🔹 Webhook-события от Telegram
# -------------------------------------------------

class TelegramWebhookUpdate(BaseModel):
    """Объект, представляющий входящее событие Telegram (message, callback и т.п.)."""

    update_id: int = Field(..., description="Уникальный идентификатор апдейта Telegram")
    message: Optional[dict] = Field(None, description="Сообщение (если тип update — message)")
    callback_query: Optional[dict] = Field(None, description="Callback-запрос от inline-кнопки")
    edited_message: Optional[dict] = Field(None, description="Изменённое сообщение")
    inline_query: Optional[dict] = Field(None, description="Inline-запрос")
    chat_join_request: Optional[dict] = Field(None, description="Запрос на вступление в группу")

    class Config:
        json_schema_extra = {
            "example": {
                "update_id": 84591321,
                "message": {
                    "message_id": 105,
                    "from": {"id": 1201, "username": "feruz"},
                    "chat": {"id": 1201, "type": "private"},
                    "text": "/start"
                }
            }
        }


# -------------------------------------------------
# 🔹 Уведомления пользователям
# -------------------------------------------------

class NotificationRequest(BaseModel):
    """Модель запроса на отправку уведомления пользователю."""

    user_id: int = Field(..., description="ID получателя уведомления (внутренний user_id)")
    text: str = Field(..., description="Текст уведомления (HTML или Markdown)")
    message_type: str = Field(
        "info",
        description="Тип уведомления: info | success | warning | error"
    )
    silent: bool = Field(False, description="Отправить без звука (silent notification)")

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": 1201,
                "text": "💰 Вы получили 0.6 UZT за выполнение задания!",
                "message_type": "success",
                "silent": False
            }
        }


# -------------------------------------------------
# 🔹 Ответ о доставке уведомления
# -------------------------------------------------

class NotificationResponse(BaseModel):
    """Ответ API после отправки уведомления пользователю."""

    ok: bool = Field(True, description="Статус отправки уведомления")
    user_id: int = Field(..., description="ID пользователя, которому доставлено уведомление")
    sent_at: datetime = Field(..., description="Время отправки")
    message_id: Optional[int] = Field(None, description="ID сообщения в Telegram (если доступен)")

    class Config:
        json_schema_extra = {
            "example": {
                "ok": True,
                "user_id": 1201,
                "sent_at": "2025-10-12T18:40:00",
                "message_id": 785
            }
        }
