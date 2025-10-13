"""
Uzinex Boost — User Events
==========================

События, связанные с пользователями системы Uzinex Boost.

Назначение:
- отражают ключевые этапы жизненного цикла пользователя;
- используются для аналитики, уведомлений и реферальных начислений;
- интегрируются с балансом, задачами и маркетингом.

Используется в:
- domain.services.user
- adapters.notifications
- adapters.analytics
- adapters.referrals
"""

from __future__ import annotations
from datetime import datetime
from pydantic import Field

from domain.events.base import DomainEvent


# -------------------------------------------------
# 🔹 Событие: Пользователь зарегистрирован
# -------------------------------------------------
class UserRegisteredEvent(DomainEvent):
    """
    Генерируется при успешной регистрации нового пользователя.
    Используется для приветственных уведомлений, активации бонусов и аналитики.
    """

    event_type: str = "user.registered"
    user_id: int = Field(..., description="ID нового пользователя")
    email: str = Field(..., description="Email пользователя")
    username: str = Field(..., description="Username пользователя")
    referral_id: int | None = Field(None, description="Если регистрация по реферальной ссылке")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# -------------------------------------------------
# 🔹 Событие: Пользователь подтвердил email
# -------------------------------------------------
class UserVerifiedEvent(DomainEvent):
    """
    Генерируется, когда пользователь успешно подтвердил свой email.
    """

    event_type: str = "user.verified"
    user_id: int
    email: str
    verified_at: datetime = Field(default_factory=datetime.utcnow)


# -------------------------------------------------
# 🔹 Событие: Пользователь обновил профиль
# -------------------------------------------------
class UserProfileUpdatedEvent(DomainEvent):
    """
    Генерируется при обновлении профиля пользователя.
    """

    event_type: str = "user.profile_updated"
    user_id: int
    username: str | None = Field(None, description="Новый username, если был изменён")
    full_name: str | None = Field(None, description="Полное имя пользователя")
    bio: str | None = Field(None, description="Описание профиля")
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# -------------------------------------------------
# 🔹 Событие: Пользователь деактивирован / заблокирован
# -------------------------------------------------
class UserDeactivatedEvent(DomainEvent):
    """
    Генерируется, когда пользователь временно заблокирован или деактивирован.
    """

    event_type: str = "user.deactivated"
    user_id: int
    reason: str | None = Field(None, description="Причина деактивации")
    deactivated_at: datetime = Field(default_factory=datetime.utcnow)


# -------------------------------------------------
# 🔹 Событие: Пользователь удалён
# -------------------------------------------------
class UserDeletedEvent(DomainEvent):
    """
    Генерируется при полном удалении пользователя из системы.
    """

    event_type: str = "user.deleted"
    user_id: int
    deleted_by_admin: bool = Field(default=False, description="Удалён ли администратором")
    deleted_at: datetime = Field(default_factory=datetime.utcnow)
