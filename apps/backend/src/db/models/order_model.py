"""
Uzinex Boost — Order Model
===========================

ORM-модель заказов (продвижения) в экосистеме Boost v2.0.

Назначение:
- хранение всех активных и завершённых заказов пользователей;
- управление параметрами кампании (цена, лимиты, ссылки);
- связь с заданиями, транзакциями и пользователями.

Используется в:
- domain.services.orders
- api.v1.routes.orders
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
    Integer,
    Boolean,
    DateTime,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base


# -------------------------------------------------
# 🔹 Статусы заказов
# -------------------------------------------------

class OrderStatus(str, enum.Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    DRAFT = "draft"


# -------------------------------------------------
# 🔹 Типы заказов
# -------------------------------------------------

class OrderType(str, enum.Enum):
    CHANNEL_SUBSCRIBE = "channel_subscribe"
    GROUP_JOIN = "group_join"
    VIDEO_VIEW = "video_view"
    OTHER = "other"


# -------------------------------------------------
# 🔹 Модель заказа
# -------------------------------------------------

class Order(Base):
    """
    Таблица заказов на продвижение (Boost Campaigns).
    """

    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)

    title: Mapped[str] = mapped_column(String(128), nullable=False)
    target_url: Mapped[str] = mapped_column(String(512), nullable=False)

    type: Mapped[OrderType] = mapped_column(Enum(OrderType), nullable=False)
    status: Mapped[OrderStatus] = mapped_column(Enum(OrderStatus), default=OrderStatus.ACTIVE, nullable=False)

    price_per_action: Mapped[float] = mapped_column(Float, nullable=False)
    total_budget: Mapped[float] = mapped_column(Float, nullable=False)
    spent_budget: Mapped[float] = mapped_column(Float, default=0.0)

    max_actions: Mapped[int] = mapped_column(Integer, nullable=False)
    completed_actions: Mapped[int] = mapped_column(Integer, default=0)

    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_visible: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # --- Связи ---
    user = relationship("User", back_populates="orders")
    tasks = relationship("Task", back_populates="order", cascade="all, delete-orphan")
    transactions = relationship("BalanceTransaction", back_populates="order", cascade="all, delete")

    # --- Методы ---
    def remaining_budget(self) -> float:
        """Возвращает остаток средств по заказу."""
        return max(self.total_budget - self.spent_budget, 0.0)

    def completion_rate(self) -> float:
        """Возвращает процент выполненных действий."""
        if self.max_actions == 0:
            return 0.0
        return round((self.completed_actions / self.max_actions) * 100, 2)

    def __repr__(self) -> str:
        return (
            f"<Order(id={self.id}, type={self.type}, status={self.status}, "
            f"budget={self.total_budget}, spent={self.spent_budget}, user_id={self.user_id})>"
        )
