"""
Uzinex Boost — Balance & Transaction Model
==========================================

ORM-модель финансовых транзакций (начисления, списания, бонусы и т.д.)
внутренней валюты UZT.

Назначение:
- хранение всех движений баланса пользователей;
- прозрачность и аудит всех начислений и списаний;
- связь с пользователями и заказами.

Используется в:
- domain.services.balance
- api.v1.routes.balance
- adapters.payments.manual
"""

from __future__ import annotations

import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Enum,
    ForeignKey,
    String,
    Float,
    DateTime,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base


# -------------------------------------------------
# 🔹 Типы операций
# -------------------------------------------------

class TransactionType(str, enum.Enum):
    DEPOSIT = "deposit"         # Пополнение баланса
    WITHDRAW = "withdraw"       # Списание (покупка)
    TASK_REWARD = "task_reward" # Заработок за выполнение
    REFERRAL_BONUS = "ref_bonus" # Бонус за приглашение
    ADMIN_ADJUST = "admin"      # Ручное изменение админом


# -------------------------------------------------
# 🔹 Модель транзакции
# -------------------------------------------------

class BalanceTransaction(Base):
    """
    Таблица всех финансовых транзакций пользователей.
    """

    __tablename__ = "balance_transactions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    order_id: Mapped[Optional[int]] = mapped_column(ForeignKey("orders.id", ondelete="SET NULL"), nullable=True)
    task_id: Mapped[Optional[int]] = mapped_column(ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True)

    amount: Mapped[float] = mapped_column(Float, nullable=False)
    type: Mapped[TransactionType] = mapped_column(Enum(TransactionType), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    balance_after: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # --- Связи ---
    user = relationship("User", back_populates="transactions")
    order = relationship("Order", back_populates="transactions", lazy="joined")
    task = relationship("Task", back_populates="transaction", lazy="joined")

    def __repr__(self) -> str:
        return (
            f"<BalanceTransaction(id={self.id}, user_id={self.user_id}, "
            f"amount={self.amount}, type={self.type}, created_at={self.created_at})>"
        )
