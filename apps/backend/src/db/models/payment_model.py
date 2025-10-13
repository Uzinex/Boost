"""
Uzinex Boost — Payment Model
=============================

ORM-модель для хранения данных о пополнениях баланса (UZT).

Назначение:
- учёт всех пополнений через чеки и платёжные методы;
- контроль статусов подтверждения (ожидание, одобрено, отклонено);
- связь с пользователем и транзакциями.

Используется в:
- domain.services.payments
- api.v1.routes.payments
- adapters.payments.manual
"""

from __future__ import annotations
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    String,
    Float,
    Enum,
    DateTime,
    ForeignKey,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from core.database import Base


# -------------------------------------------------
# 🔹 Статусы платежей
# -------------------------------------------------

class PaymentStatus(str, enum.Enum):
    PENDING = "pending"      # Ожидает подтверждения
    VERIFIED = "verified"    # Подтвержден админом
    REJECTED = "rejected"    # Отклонен


# -------------------------------------------------
# 🔹 Методы пополнения
# -------------------------------------------------

class PaymentMethod(str, enum.Enum):
    CLICK = "click"          # Click
    PAYME = "payme"          # Payme
    CARD = "card"            # Ручной ввод карты
    MANUAL = "manual"        # Фото чека вручную
    OTHER = "other"          # Другое


# -------------------------------------------------
# 🔹 Модель платежа
# -------------------------------------------------

class Payment(Base):
    """
    Таблица пополнений баланса пользователей.
    """

    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)

    amount: Mapped[float] = mapped_column(Float, nullable=False)
    method: Mapped[PaymentMethod] = mapped_column(Enum(PaymentMethod), nullable=False)
    status: Mapped[PaymentStatus] = mapped_column(Enum(PaymentStatus), default=PaymentStatus.PENDING)
    reference: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)  # ID из Click/Payme или вручную
    screenshot_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)  # URL на чек
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    verified_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # --- Связи ---
    user = relationship("User", foreign_keys=[user_id], back_populates="payments")
    verifier = relationship("User", foreign_keys=[verified_by])
    transactions = relationship("BalanceTransaction", back_populates="payment", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return (
            f"<Payment(id={self.id}, user_id={self.user_id}, amount={self.amount}, "
            f"status={self.status}, method={self.method})>"
        )
