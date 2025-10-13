"""Custom exceptions raised by the Telegram bot service layer."""

from __future__ import annotations


class BotServiceError(RuntimeError):
    """Base error for bot service related failures."""


class WebAppAuthError(BotServiceError):
    """Raised when the Telegram WebApp authorisation flow fails."""


class NotificationDeliveryError(BotServiceError):
    """Raised when the service fails to deliver a Telegram notification."""


__all__ = [
    "BotServiceError",
    "NotificationDeliveryError",
    "WebAppAuthError",
]
