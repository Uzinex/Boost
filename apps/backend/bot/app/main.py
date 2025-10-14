"""Uzinex Boost — Telegram bot standalone entrypoint."""

import asyncio

from loguru import logger

from bot import bot, dp


async def start_bot() -> None:
    """Запуск поллинга Telegram-бота в standalone-режиме."""

    logger.info("🤖 Bot polling started...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(start_bot())
