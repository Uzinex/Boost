"""
Uzinex Boost — Telegram Data Types
==================================

Модели данных для Telegram-интеграции:
- TelegramUser
- TelegramChat
- TelegramMessage
- WebAppData (initData)
- TelegramCallback

Используются для типизации, сериализации и валидации
внутри адаптера Telegram и API-слоёв.
"""

from __future__ import annotations

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


# ----------------------------
# 🔹 Telegram базовые модели
# ----------------------------

class TelegramUser(BaseModel):
    """Модель Telegram-пользователя (из update или initData)."""

    id: int = Field(..., description="Telegram user ID")
    is_bot: Optional[bool] = False
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    username: Optional[str] = None
    language_code: Optional[str] = None
    is_premium: Optional[bool] = None

    def full_name(self) -> str:
        parts = [self.first_name or "", self.last_name or ""]
        return " ".join(p for p in parts if p).strip() or "Unknown User"

    def mention(self) -> str:
        """Возвращает HTML-ссылку на пользователя."""
        if self.username:
            return f"@{self.username}"
        return f"<a href='tg://user?id={self.id}'>{self.full_name()}</a>"


class TelegramChat(BaseModel):
    """Модель чата (private / group / channel)."""

    id: int
    type: str
    title: Optional[str] = None
    username: Optional[str] = None


class TelegramMessage(BaseModel):
    """Модель сообщения (используется для логирования и callback)."""

    message_id: int
    date: datetime
    chat: TelegramChat
    from_user: TelegramUser
    text: Optional[str] = None


# ----------------------------
# 🔹 WebApp модели
# ----------------------------

class WebAppUser(BaseModel):
    """Telegram WebApp user из initData."""

    id: int
    first_name: Optional[str]
    last_name: Optional[str]
    username: Optional[str]
    language_code: Optional[str]
    is_premium: Optional[bool] = None

    def full_name(self) -> str:
        parts = [self.first_name or "", self.last_name or ""]
        return " ".join(p for p in parts if p).strip()


class WebAppData(BaseModel):
    """
    Данные, получаемые из Telegram WebApp initData.
    Используются для авторизации пользователей.
    """

    user: WebAppUser
    auth_date: int
    query_id: Optional[str] = None
    hash: str

    def to_dict(self) -> Dict[str, Any]:
        """Преобразует объект в dict (для валидации и логирования)."""
        return self.model_dump()

    def auth_datetime(self) -> datetime:
        """Возвращает auth_date в виде datetime UTC."""
        return datetime.utcfromtimestamp(self.auth_date)


# ----------------------------
# 🔹 Callback / Interaction модели
# ----------------------------

class TelegramCallback(BaseModel):
    """CallbackQuery объект для inline-кнопок."""

    id: str
    from_user: TelegramUser = Field(..., alias="from")
    data: Optional[str] = None
    chat_instance: Optional[str] = None


# ----------------------------
# 🔹 Результаты валидации
# ----------------------------

class WebAppValidationResult(BaseModel):
    """Результат проверки initData."""

    valid: bool
    reason: Optional[str] = None
    user_id: Optional[int] = None
    username: Optional[str] = None
    auth_datetime: Optional[datetime] = None


# ----------------------------
# 🔹 Экспорт
# ----------------------------

__all__ = [
    "TelegramUser",
    "TelegramChat",
    "TelegramMessage",
    "WebAppUser",
    "WebAppData",
    "TelegramCallback",
    "WebAppValidationResult",
]
