"""Logging middleware simplifying observability for handlers."""

from __future__ import annotations

import logging
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

Handler = Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]]


class LoggingMiddleware(BaseMiddleware):
    """Log incoming updates and unhandled exceptions."""

    def __init__(
        self,
        logger: logging.Logger | None = None,
        *,
        log_success: bool = False,
    ) -> None:
        self._logger = logger or logging.getLogger("boost.bot.middleware.logging")
        self._log_success = log_success

    async def __call__(
        self,
        handler: Handler,
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        event_name = event.__class__.__name__
        self._logger.debug("Handling update: %s", event_name)
        try:
            result = await handler(event, data)
        except Exception:
            self._logger.exception("Unhandled error during handling of %s", event_name)
            raise
        if self._log_success:
            self._logger.debug("Successfully handled update: %s", event_name)
        return result
