"""
Uzinex Boost — Referral Model
==============================

ORM-модель для хранения реферальных связей пользователей.

Назначение:
- хранение данных о том, кто кого пригласил;
- учёт бонусов за приглашения (UZT);
- связь с пользователем (referred и referrer);
- используется при начислении `REFERRAL_BONUS` в транзакциях.

Используется в:
- domain.services.referrals
- api.v1.routes.users
- balance/transaction logic
"""

from __future__ import annotations
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    ForeignKey,
    Float,
    DateTime,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base



# -------------------------------------------------
# 🔹 Модель рефералов
# -------------------------------------------------

class Referral(Base):
    """
    Таблица реферальных связей пользователей.
    """

    __tablename__ = "referrals"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    referrer_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    referred_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True
    )

    joined_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    bonus_amount: Mapped[Optional[float]] = mapped_column(Float, default=0.0)

    # --- Связи ---
    referrer = relationship(
        "User",
        foreign_keys=[referrer_id],
        back_populates="referrals_invited",
    )
    referred = relationship(
        "User",
        foreign_keys=[referred_id],
        back_populates="referral_source",
    )

    def __repr__(self) -> str:
        return (
            f"<Referral(id={self.id}, referrer_id={self.referrer_id}, "
            f"referred_id={self.referred_id}, bonus={self.bonus_amount})>"
        )
