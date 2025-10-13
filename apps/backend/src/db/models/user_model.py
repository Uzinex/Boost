"""
Uzinex Boost — User Model
==========================

ORM-модель Telegram-пользователя платформы Boost v2.0.

Назначение:
- хранение базовой информации о пользователях;
- учёт баланса UZT;
- связи с заказами, заданиями, платежами и рефералами;
- поддержка Telegram WebApp авторизации.

Используется в:
- domain.services.users
- api.v1.routes.users
- adapters.telegram.webapp_auth
"""

from __future__ import annotations
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    String,
    Float,
    DateTime,
    Boolean,
    ForeignKey,
    Integer,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base


class User(Base):
    """
    Таблица Telegram-пользователей.
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    telegram_id: Mapped[int] = mapped_column(unique=True, index=True)
    username: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    first_name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    language_code: Mapped[str] = mapped_column(String(8), default="ru")

    balance: Mapped[float] = mapped_column(Float, default=0.0)
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)

    referrer_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_active_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # --- Связи ---
    referrer = relationship("User", remote_side=[id], back_populates="referrals_invited_parent")

    orders = relationship("Order", back_populates="user", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="user", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="user", cascade="all, delete-orphan")
    transactions = relationship("BalanceTransaction", back_populates="user", cascade="all, delete-orphan")

    # Реферальные связи
    referrals_invited = relationship(
        "Referral",
        foreign_keys="Referral.referrer_id",
        back_populates="referrer",
        cascade="all, delete-orphan",
    )
    referral_source = relationship(
        "Referral",
        foreign_keys="Referral.referred_id",
        back_populates="referred",
        uselist=False,
    )

    def __repr__(self) -> str:
        return (
            f"<User(id={self.id}, telegram_id={self.telegram_id}, username={self.username}, "
            f"balance={self.balance:.2f}, admin={self.is_admin})>"
        )

    # -------------------------------------------------
    # 🔹 Утилиты (бизнес-логика ORM уровня)
    # -------------------------------------------------

    def add_balance(self, amount: float) -> None:
        """Начисляет пользователю UZT."""
        self.balance += amount

    def deduct_balance(self, amount: float) -> bool:
        """Списывает UZT, если хватает средств."""
        if self.balance >= amount:
            self.balance -= amount
            return True
        return False

    def mark_active(self) -> None:
        """Обновляет время последней активности."""
        self.last_active_at = datetime.utcnow()
