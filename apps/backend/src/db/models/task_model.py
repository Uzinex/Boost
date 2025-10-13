"""
Uzinex Boost — Task Model
==========================

ORM-модель для хранения заданий, выполняемых пользователями.

Назначение:
- представление конкретных действий (подписка, вступление, просмотр);
- учёт статуса выполнения;
- связь с пользователем, заказом и транзакцией.

Используется в:
- domain.services.tasks
- api.v1.routes.tasks
- adapters.telegram.notifier
"""

from __future__ import annotations
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    ForeignKey,
    Enum,
    DateTime,
    Float,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from db.base import Base



# -------------------------------------------------
# 🔹 Статусы заданий
# -------------------------------------------------

class TaskStatus(str, enum.Enum):
    PENDING = "pending"     # Назначено пользователю, ждёт выполнения
    COMPLETED = "completed" # Выполнено и проверено
    REJECTED = "rejected"   # Отклонено (например, ботом или админом)


# -------------------------------------------------
# 🔹 Модель задания
# -------------------------------------------------

class Task(Base):
    """
    Таблица заданий, выполняемых пользователями.
    """

    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)

    reward_amount: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    status: Mapped[TaskStatus] = mapped_column(Enum(TaskStatus), default=TaskStatus.PENDING)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # --- Связи ---
    user = relationship("User", back_populates="tasks")
    order = relationship("Order", back_populates="tasks")
    transaction = relationship("BalanceTransaction", back_populates="task", uselist=False)

    def __repr__(self) -> str:
        return (
            f"<Task(id={self.id}, user_id={self.user_id}, order_id={self.order_id}, "
            f"status={self.status}, reward={self.reward_amount})>"
        )
