"""Data transfer objects used by :mod:`bot.app.service`."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass(slots=True)
class TelegramUserSnapshot:
    """A lightweight representation of a Telegram user stored in the database."""

    id: int
    telegram_id: int
    username: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    language_code: str | None = None
    balance: float = 0.0
    is_admin: bool = False
    is_banned: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Return a serialisable representation of the snapshot."""

        return {
            "id": self.id,
            "telegram_id": self.telegram_id,
            "username": self.username,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "language": self.language_code,
            "balance": self.balance,
            "is_admin": self.is_admin,
            "is_banned": self.is_banned,
        }


@dataclass(slots=True)
class WebAppAuthResult:
    """Result produced after successful Telegram WebApp authorisation."""

    session_token: str
    user: TelegramUserSnapshot
    raw_payload: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-ready dictionary for API responses."""

        return {
            "ok": True,
            "session_token": self.session_token,
            "user": self.user.to_dict(),
        }


@dataclass(slots=True)
class NotificationResult:
    """Represents a result of sending a notification to a Telegram user."""

    delivered: bool
    user_id: int | str
    message_type: str
    text: str

    def to_dict(self) -> dict[str, Any]:
        """Return a serialisable representation of the notification result."""

        return {
            "ok": self.delivered,
            "user_id": self.user_id,
            "message_type": self.message_type,
            "text": self.text,
        }


@dataclass(slots=True)
class ManualDepositResult:
    """Represents the outcome of creating a manual deposit request."""

    ok: bool
    status: str
    payment_id: int | None = None
    message: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Return the result as a JSON compatible dictionary."""

        payload = {
            "ok": self.ok,
            "status": self.status,
        }
        if self.payment_id is not None:
            payload["payment_id"] = self.payment_id
        if self.message:
            payload["message"] = self.message
        return payload


__all__ = [
    "ManualDepositResult",
    "NotificationResult",
    "TelegramUserSnapshot",
    "WebAppAuthResult",
]
