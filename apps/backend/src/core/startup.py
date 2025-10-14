"""
Uzinex Boost — Startup Initialization
====================================

Инициализация ключевых компонентов приложения:
- PostgreSQL
- Redis
- Telegram Bot
- Логирование и системные проверки
"""

from __future__ import annotations

import asyncio
import logging
from core.database import engine
from adapters.cache.redis_cache import RedisCache
from adapters.telegram.client import TelegramClient
from core.config import settings

logger = logging.getLogger("uzinex.core.startup")


async def init_app() -> None:
    """
    Выполняет первичную инициализацию инфраструктуры Uzinex Boost:
    БД, кэш, Telegram, сервисы.
    """
    logger.info("🚀 Starting Uzinex Boost initialization sequence...")

    # -------------------------------
    # PostgreSQL
    # -------------------------------
    try:
        async with engine.begin() as conn:
            await conn.run_sync(lambda _: None)
        db_ok = True
        logger.info("🗄 PostgreSQL connection: ✅ OK")
    except Exception as e:
        db_ok = False
        logger.error(f"❌ PostgreSQL connection failed: {e}")

    # -------------------------------
    # Redis
    # -------------------------------
    redis_ok = False
    redis_url = (
        settings.REDIS_URL
        or f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}"
    )

    redis_cache = RedisCache(url=redis_url)
    try:
        await redis_cache.connect()
        ping_result = await redis_cache.ping()
        redis_ok = ping_result
        if redis_ok:
            logger.info(f"✅ Connected to Redis ({redis_url})")
        else:
            logger.warning("⚠️ Redis ping failed but connection established.")
    except Exception as e:
        logger.error(f"❌ Redis connection failed: {e}")

    # -------------------------------
    # Telegram Bot
    # -------------------------------
    telegram_ok = False
    telegram_token = getattr(settings, "TELEGRAM_BOT_TOKEN", None)

    if telegram_token:
        telegram_client = TelegramClient(token=telegram_token)
        try:
            me = await telegram_client.get_me()
            username = me.get("username", "unknown")
            bot_id = me.get("id", "N/A")
            logger.info(f"🤖 Telegram bot connected: @{username} (id={bot_id})")
            telegram_ok = True
        except Exception as e:
            logger.warning(f"⚠️ Telegram bot check skipped or failed: {e}")
        finally:
            await telegram_client.close()
    else:
        logger.warning("⚠️ Telegram token not provided — bot skipped.")

    # -------------------------------
    # Summary
    # -------------------------------
    logger.info(
        f"System summary → DB: {db_ok} | Redis: {redis_ok} | Telegram: {telegram_ok}"
    )
    logger.info("✅ Startup checks completed successfully.")
