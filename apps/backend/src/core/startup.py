"""
Uzinex Boost Core — Startup Sequence
====================================

Инициализация всех инфраструктурных компонентов системы:
- PostgreSQL
- Redis
- Telegram Bot
- Кэш и логирование
"""

from __future__ import annotations
import logging
import asyncio

from core.database import engine
from core.config import settings
from adapters.cache.redis_cache import RedisCache
from adapters.telegram.client import TelegramClient

logger = logging.getLogger("uzinex.core.startup")


async def init_app() -> None:
    """
    Выполняет поочередную инициализацию всех основных компонентов.
    Проверяет подключение к PostgreSQL, Redis и Telegram Bot API.
    """
    logger.info("🚀 Starting Uzinex Boost initialization sequence...")

    db_ok = False
    redis_ok = False
    telegram_ok = None

    # -------------------------------------------------
    # 🗄 Проверка PostgreSQL
    # -------------------------------------------------
    try:
        async with engine.begin() as conn:
            await conn.run_sync(lambda _: None)
        logger.info("🗄 PostgreSQL connection: ✅ OK")
        db_ok = True
    except Exception as e:
        logger.error(f"❌ PostgreSQL connection failed: {e}")

    # -------------------------------------------------
    # 🧠 Проверка Redis
    # -------------------------------------------------
    try:
        cache = RedisCache()
        await cache.ping()
        logger.info(f"✅ Connected to Redis ({settings.REDIS_URL})")
        redis_ok = True
    except Exception as e:
        logger.error(f"❌ Redis connection failed: {e}")

    # -------------------------------------------------
    # 🔹 Проверка Telegram Bot
    # -------------------------------------------------
    try:
        me = await telegram_client.get_me()
        username = me.get("username", "unknown")
        bot_id = me.get("id", "N/A")
        logger.info(f"🤖 Telegram bot connected: @{username} (id={bot_id})")
        telegram_ok = True
    except Exception as e:
        telegram_ok = False
        logger.warning(f"⚠️ Telegram bot check skipped or failed: {e}")


    # -------------------------------------------------
    # 🧩 Финальный отчёт
    # -------------------------------------------------
    summary = f"System summary → DB: {db_ok} | Redis: {redis_ok} | Telegram: {telegram_ok}"
    logger.info(summary)
    logger.info("✅ Startup checks completed successfully.")


__all__ = ["init_app"]
