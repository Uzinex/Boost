"""Application configuration for the Telegram bot."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Tuple

from os import getenv


@dataclass(slots=True)
class BotSettings:
    """Settings holder for the Telegram bot."""

    bot_token: str
    backend_url: str
    backend_token: str | None = None
    admin_ids: Tuple[int, ...] = field(default_factory=tuple)
    default_language: str = "ru"
    request_timeout: float = 10.0

    @classmethod
    def from_env(cls) -> "BotSettings":
        """Create settings instance by reading environment variables."""
        raw_admins = getenv("BOOST_BOT_ADMIN_IDS", "")
        admin_ids: Tuple[int, ...] = tuple(
            int(admin.strip())
            for admin in raw_admins.split(",")
            if admin.strip().isdigit()
        )

        bot_token = getenv("BOOST_BOT_TOKEN")
        backend_url = getenv("BOOST_BACKEND_URL")
        backend_token = getenv("BOOST_BOT_BACKEND_TOKEN")
        default_language = getenv("BOOST_BOT_DEFAULT_LANG", "ru").lower()
        timeout_raw = getenv("BOOST_BOT_TIMEOUT", "10.0")

        if not bot_token:
            raise RuntimeError("Environment variable BOOST_BOT_TOKEN is required")

        if not backend_url:
            raise RuntimeError("Environment variable BOOST_BACKEND_URL is required")

        try:
            timeout = float(timeout_raw)
        except ValueError as exc:
            raise RuntimeError("BOOST_BOT_TIMEOUT must be a numeric value") from exc

        return cls(
            bot_token=bot_token,
            backend_url=backend_url.rstrip("/"),
            backend_token=backend_token,
            admin_ids=admin_ids,
            default_language=default_language,
            request_timeout=timeout,
        )


settings = BotSettings.from_env()
