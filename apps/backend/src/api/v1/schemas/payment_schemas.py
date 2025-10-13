"""
Uzinex Boost API v1 — Payment Schemas
=====================================

Схемы данных для операций пополнения и управления транзакциями.

Назначение:
- создание заявок на пополнение;
- получение статуса пополнения;
- история транзакций (пополнения / возвраты);
- связь с балансом пользователя (UZT).
"""

from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional

from .base import IDMixin, TimestampMixin


# -------------------------------------------------
# 🔹 Запрос на пополнение
# -------------------------------------------------

class PaymentCreateRequest(BaseModel):
    """Запрос на создание новой заявки на пополнение."""

    amount_uzt: float = Field(..., gt=0, description="Сумма пополнения в UZT")
    check_photo_url: str = Field(..., description="Ссылка или FileID чека (Telegram)")
    payment_method: str = Field("manual", description="Метод оплаты: manual | click | payme")

    class Config:
        json_schema_extra = {
            "example": {
                "amount_uzt": 250.0,
                "check_photo_url": "https://t.me/c/123456/789",
                "payment_method": "manual"
            }
        }


# -------------------------------------------------
# 🔹 Ответ о статусе пополнения
# -------------------------------------------------

class PaymentStatusResponse(IDMixin, TimestampMixin):
    """Возвращает информацию о статусе заявки на пополнение."""

    user_id: int = Field(..., description="ID пользователя, сделавшего заявку")
    amount_uzt: float = Field(..., description="Сумма пополнения в UZT")
    status: str = Field(..., description="Статус пополнения: pending | confirmed | rejected | canceled")
    method: str = Field(..., description="Метод оплаты (manual, click, payme)")
    comment: Optional[str] = Field(None, description="Комментарий администратора")
    verified_by: Optional[int] = Field(None, description="ID админа, подтвердившего оплату")

    class Config:
        orm_mode = True
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "inv_20251012_987654",
                "user_id": 42,
                "amount_uzt": 300.0,
                "status": "pending",
                "method": "manual",
                "comment": None,
                "verified_by": None,
                "created_at": "2025-10-12T18:00:00",
                "updated_at": "2025-10-12T18:10:00"
            }
        }


# -------------------------------------------------
# 🔹 История пополнений
# -------------------------------------------------

class PaymentHistoryRecord(BaseModel):
    """Запись истории операций по пополнениям пользователя."""

    id: str = Field(..., description="Уникальный идентификатор инвойса")
    amount_uzt: float = Field(..., description="Сумма пополнения (UZT)")
    status: str = Field(..., description="Статус пополнения")
    created_at: datetime = Field(..., description="Дата создания инвойса")
    confirmed_at: Optional[datetime] = Field(None, description="Дата подтверждения")
    method: str = Field("manual", description="Метод оплаты")
    comment: Optional[str] = Field(None, description="Комментарий администратора")

    class Config:
        orm_mode = True
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "inv_20251012_987654",
                "amount_uzt": 250.0,
                "status": "confirmed",
                "method": "manual",
                "comment": "Пополнение через чек",
                "created_at": "2025-10-12T16:45:00",
                "confirmed_at": "2025-10-12T17:00:00"
            }
        }
