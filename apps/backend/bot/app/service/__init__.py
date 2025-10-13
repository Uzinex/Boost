"""Service layer that bridges the backend domain with the Telegram bot."""

from .bot_service import BotService
from .contracts import (
    ManualDepositResult,
    NotificationResult,
    TelegramUserSnapshot,
    WebAppAuthResult,
)
from .exceptions import (
    BotServiceError,
    NotificationDeliveryError,
    WebAppAuthError,
)

__all__ = [
    "BotService",
    "BotServiceError",
    "NotificationDeliveryError",
    "WebAppAuthError",
    "ManualDepositResult",
    "NotificationResult",
    "TelegramUserSnapshot",
    "WebAppAuthResult",
]
