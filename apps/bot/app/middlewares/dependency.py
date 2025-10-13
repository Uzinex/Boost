"""Dependency injection middleware for aiogram handlers."""

from __future__ import annotations

from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from ..config import BotSettings
from ..service.api import BoostAPIClient

Handler = Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]]


class DependencyInjectionMiddleware(BaseMiddleware):
    """Populate handler context with shared application services."""

    def __init__(self, *, settings: BotSettings, api_client: BoostAPIClient) -> None:
        self._settings = settings
        self._api_client = api_client

    async def __call__(
        self,
        handler: Handler,
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        data.setdefault("settings", self._settings)
        data.setdefault("api_client", self._api_client)
        return await handler(event, data)
