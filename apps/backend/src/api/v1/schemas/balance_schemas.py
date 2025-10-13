"""
Uzinex Boost API v1 — Balance Schemas
=====================================

Схемы данных, связанные с балансом и UZT-транзакциями.

Назначение:
- сериализация данных о балансе пользователя;
- представление транзакций (пополнение, списание, вознаграждение);
- использование в эндпоинтах /balance, /payments, /orders, /tasks.
"""

from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, Field


# -------------------------------------------------
# 🔹 Транзакция (отдельная операция)
# -------------------------------------------------

class TransactionRecord(BaseModel):
    """Модель отдельной операции (пополнение, списание, награда)."""

    id: int = Field(..., description="ID транзакции")
    type: str = Field(..., description="Тип операции: deposit | withdraw | reward | refund")
    amount: float = Field(..., description="Сумма операции в UZT (положительная или отрицательная)")
    description: str | None = Field(None, description="Комментарий или источник операции")
    created_at: datetime = Field(..., description="Дата и время операции")

    class Config:
        orm_mode = True
        from_attributes = True


# -------------------------------------------------
# 🔹 Баланс пользователя
# -------------------------------------------------

class BalanceResponse(BaseModel):
    """Ответ с текущим балансом и краткой историей операций."""

    user_id: int = Field(..., description="ID пользователя")
    balance: float = Field(..., ge=0, description="Текущий баланс пользователя (UZT)")
    updated_at: datetime = Field(..., description="Дата последнего обновления баланса")
    recent_transactions: list[TransactionRecord] | None = Field(
        default_factory=list,
        description="Последние транзакции пользователя",
    )

    class Config:
        orm_mode = True
        from_attributes = True


# -------------------------------------------------
# 🔹 Запрос на пополнение (используется в /payments/manual)
# -------------------------------------------------

class TopUpRequest(BaseModel):
    """Модель запроса на пополнение баланса вручную."""

    amount: float = Field(..., gt=0, description="Сумма пополнения в UZT")
    check_photo_url: str = Field(..., description="Ссылка на чек (Telegram FileID или URL)")
    payment_method: str | None = Field("manual", description="Метод оплаты (manual | click | payme)")

    class Config:
        schema_extra = {
            "example": {
                "amount": 250.0,
                "check_photo_url": "https://t.me/c/123456/789",
                "payment_method": "manual"
            }
        }
