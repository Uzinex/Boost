"""
Uzinex Boost API v1 — User Schemas
===================================

Схемы данных для работы с пользователями:
- регистрация и авторизация через Telegram WebApp;
- получение и обновление профиля;
- реферальная система и пользовательская статистика.

Используется в: /users, /auth, /stats, /balance.
"""

from __future__ import annotations
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

from .base import IDMixin, TimestampMixin


# -------------------------------------------------
# 🔹 Краткая информация о пользователе
# -------------------------------------------------

class UserRead(IDMixin, TimestampMixin):
    """Базовая информация о пользователе."""

    username: Optional[str] = Field(None, description="Telegram username пользователя")
    first_name: Optional[str] = Field(None, description="Имя пользователя (из Telegram)")
    language: str = Field("ru", description="Предпочитаемый язык интерфейса")
    balance: float = Field(0.0, description="Текущий баланс (UZT)")
    is_active: bool = Field(True, description="Флаг активности пользователя")
    referrer_id: Optional[int] = Field(None, description="ID пригласившего пользователя")

    class Config:
        orm_mode = True
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1201,
                "username": "feruz",
                "first_name": "Feruz",
                "language": "uz",
                "balance": 154.6,
                "is_active": True,
                "referrer_id": 42,
                "created_at": "2025-10-12T14:00:00",
                "updated_at": "2025-10-12T15:10:00"
            }
        }


# -------------------------------------------------
# 🔹 Обновление профиля
# -------------------------------------------------

class UserUpdate(BaseModel):
    """Модель для обновления профиля пользователя."""

    username: Optional[str] = Field(None, description="Telegram username (если пользователь хочет изменить)")
    language: Optional[str] = Field(None, description="Предпочитаемый язык интерфейса: uz | ru | en")

    class Config:
        json_schema_extra = {
            "example": {
                "username": "nexar",
                "language": "uz"
            }
        }


# -------------------------------------------------
# 🔹 Ответ с профилем пользователя
# -------------------------------------------------

class UserProfileResponse(BaseModel):
    """Ответ API при запросе профиля пользователя."""

    ok: bool = Field(True, description="Флаг успешности операции")
    user: UserRead = Field(..., description="Информация о пользователе")

    class Config:
        json_schema_extra = {
            "example": {
                "ok": True,
                "user": {
                    "id": 1201,
                    "username": "feruz",
                    "first_name": "Feruz",
                    "language": "uz",
                    "balance": 154.6,
                    "is_active": True,
                    "referrer_id": 42,
                    "created_at": "2025-10-12T14:00:00",
                    "updated_at": "2025-10-12T15:10:00"
                }
            }
        }


# -------------------------------------------------
# 🔹 Реферальная система
# -------------------------------------------------

class ReferralUser(BaseModel):
    """Упрощённая модель для представления реферала."""

    id: int = Field(..., description="ID реферала")
    username: Optional[str] = Field(None, description="Telegram username реферала")
    joined_at: datetime = Field(..., description="Дата регистрации реферала")

    class Config:
        orm_mode = True
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 2022,
                "username": "aziza",
                "joined_at": "2025-10-12T13:45:00"
            }
        }


class UserReferralsResponse(BaseModel):
    """Ответ API со списком рефералов пользователя."""

    ok: bool = Field(True, description="Флаг успешности операции")
    count: int = Field(..., description="Количество рефералов")
    referrals: List[ReferralUser] = Field(..., description="Список рефералов")

    class Config:
        json_schema_extra = {
            "example": {
                "ok": True,
                "count": 2,
                "referrals": [
                    {"id": 2022, "username": "aziza", "joined_at": "2025-10-12T13:45:00"},
                    {"id": 2041, "username": "dilshod", "joined_at": "2025-10-12T14:05:00"}
                ]
            }
        }


# -------------------------------------------------
# 🔹 Ответ при удалении аккаунта
# -------------------------------------------------

class UserDeleteResponse(BaseModel):
    """Ответ API при успешном удалении аккаунта."""

    ok: bool = Field(True, description="Флаг успешности")
    message: str = Field("Account deleted", description="Сообщение о результате операции")

    class Config:
        json_schema_extra = {
            "example": {
                "ok": True,
                "message": "Account deleted"
            }
        }
