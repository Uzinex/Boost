"""
Uzinex Boost — Referral Events
==============================

События, связанные с реферальной системой платформы Uzinex Boost.

Назначение:
-----------
- фиксируют все ключевые действия в реферальной сети;
- позволяют начислять бонусы и строить аналитику роста сообщества;
- интегрируются с балансом и пользовательскими событиями.

Используется в:
---------------
- domain.services.referral
- domain.services.balance
- adapters.analytics
- adapters.notifications
"""

from __future__ import annotations
from datetime import datetime
from pydantic import Field

from domain.events.base import DomainEvent


# -------------------------------------------------
# 🔹 Событие: Новый реферал приглашён
# -------------------------------------------------
class ReferralInvitedEvent(DomainEvent):
    """Генерируется, когда пользователь отправил приглашение новому участнику."""

    event_type: str = "referral.invited"
    inviter_id: int = Field(..., description="ID пользователя, пригласившего нового участника")
    invitee_email: str = Field(..., description="Email приглашённого пользователя")
    invite_code: str = Field(..., description="Код приглашения или ссылка")
    invited_at: datetime = Field(default_factory=datetime.utcnow)


# -------------------------------------------------
# 🔹 Событие: Новый реферал зарегистрировался (добавлено)
# -------------------------------------------------
class ReferralRegisteredEvent(DomainEvent):
    """Генерируется, когда приглашённый пользователь завершает регистрацию."""

    event_type: str = "referral.registered"
    inviter_id: int = Field(..., description="ID пользователя, пригласившего реферала")
    referral_id: int = Field(..., description="ID нового зарегистрированного пользователя")
    referral_email: str | None = Field(None, description="Email нового пользователя (если есть)")
    registered_at: datetime = Field(default_factory=datetime.utcnow)


# -------------------------------------------------
# 🔹 Событие: Новый реферал присоединился
# -------------------------------------------------
class ReferralJoinedEvent(DomainEvent):
    """Генерируется, когда приглашённый пользователь успешно зарегистрировался."""

    event_type: str = "referral.joined"
    inviter_id: int
    referral_id: int = Field(..., description="ID нового реферала")
    joined_at: datetime = Field(default_factory=datetime.utcnow)


# -------------------------------------------------
# 🔹 Событие: Реферальный бонус начислен
# -------------------------------------------------
class ReferralRewardedEvent(DomainEvent):
    """Генерируется, когда пользователю начисляется бонус за активность его реферала."""

    event_type: str = "referral.rewarded"
    inviter_id: int = Field(..., description="ID пользователя, получившего бонус")
    referral_id: int = Field(..., description="ID реферала, за которого начислен бонус")
    amount: float = Field(..., description="Сумма бонуса (UZT)")
    reason: str = Field(..., description="Причина бонуса (signup, task_completed, deposit и т.д.)")
    transaction_id: int | None = Field(None, description="ID связанной транзакции")
    rewarded_at: datetime = Field(default_factory=datetime.utcnow)


# -------------------------------------------------
# 🔹 Событие: Достигнут новый уровень реферальной программы
# -------------------------------------------------
class ReferralLevelUpEvent(DomainEvent):
    """Генерируется, когда пользователь достигает нового уровня реферальной программы."""

    event_type: str = "referral.level_up"
    user_id: int = Field(..., description="ID пользователя, достигшего нового уровня")
    new_level: int = Field(..., description="Новый уровень в реферальной системе")
    bonus_amount: float = Field(default=0.0, description="Бонус за повышение уровня, если есть")
    achieved_at: datetime = Field(default_factory=datetime.utcnow)
