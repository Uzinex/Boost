"""Entry point for running the Boost Telegram bot."""

from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode

from .config import settings
from .handlers import admin, payments, start
from .service.api import BoostAPIClient


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )


async def main() -> None:
    """Run the bot dispatcher."""

    setup_logging()
    logger = logging.getLogger("boost.bot")

    bot = Bot(token=settings.bot_token, parse_mode=ParseMode.HTML)
    api_client = BoostAPIClient(
        base_url=settings.backend_url,
        token=settings.backend_token,
        timeout=settings.request_timeout,
    )

    dispatcher = Dispatcher()
    dispatcher.include_router(start.router)
    dispatcher.include_router(payments.router)
    dispatcher.include_router(admin.router)

    bot["settings"] = settings
    bot["api_client"] = api_client

    logger.info("Boost bot is starting...")

    try:
        await dispatcher.start_polling(bot)
    finally:
        await api_client.aclose()
        await bot.session.close()
        logger.info("Boost bot stopped.")


if __name__ == "__main__":  # pragma: no cover - entry point
    asyncio.run(main())
