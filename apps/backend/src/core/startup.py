"""
Uzinex Boost Core — Startup Initialization
===========================================

Модуль инициализации ядра при запуске приложения.

Функционал:
- Проверка соединения с PostgreSQL и Redis
- Проверка доступности Telegram API (опционально)
- Инициализация логирования и конфигурации
- Вывод диагностической информации (версия, окружение, билд)
- Прогрев кэша и других зависимостей при старте FastAPI / Worker

Используется при старте backend (FastAPI) и бота.
"""

from __future__ import annotations

import asyncio
import logging
import time
import aiohttp

from core import settings, get_logger
from core.database import test_database_connection
from adapters.cache.redis_cache import RedisCache

logger = get_logger("uzinex.core.startup")


# -------------------------------------------------
# 🔹 System startup
# -------------------------------------------------

async def init_startup_checks() -> None:
    """
    Проверяет основные системные зависимости при старте.
    Используется FastAPI event handler'ом (on_startup).
    """
    logger.info("🚀 Starting Uzinex Boost initialization sequence...")

    start_time = time.time()
    results = {"database": False, "redis": False, "telegram": None}

    # --- Проверка PostgreSQL ---
    db_ok = await test_database_connection()
    results["database"] = db_ok
    logger.info(f"🗄 PostgreSQL connection: {'✅ OK' if db_ok else '❌ FAIL'}")

    # --- Проверка Redis ---
    try:
        cache = RedisCache()
        await cache.connect()
        results["redis"] = await cache.ping()
        await cache.close()
    except Exception as e:
        logger.error(f"Redis initialization failed: {e}")
        results["redis"] = False

    logger.info(f"🧠 Redis connection: {'✅ OK' if results['redis'] else '❌ FAIL'}")

    # --- Проверка Telegram Bot API (опционально) ---
    if settings.TELEGRAM_DEBUG_MODE:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/getMe"
                ) as resp:
                    results["telegram"] = resp.status == 200
        except Exception as e:
            results["telegram"] = False
            logger.warning(f"Telegram check skipped or failed: {e}")
        logger.info(f"🤖 Telegram API: {'✅ OK' if results['telegram'] else '⚠️ SKIPPED'}")

    # --- Резюме и вывод статистики ---
    duration = round(time.time() - start_time, 2)
    logger.info(f"✅ Startup checks completed in {duration}s")
    logger.info(
        f"System summary → DB: {results['database']} | Redis: {results['redis']} | Telegram: {results['telegram']}"
    )

    if not results["database"] or not results["redis"]:
        logger.warning("⚠️ Some dependencies failed — application may not work correctly!")


# -------------------------------------------------
# 🔹 Optional: preloading / cache warming
# -------------------------------------------------

async def warm_up_cache() -> None:
    """
    Прогревает кэш при старте (например, справочники, тарифы, метаданные).
    """
    try:
        cache = RedisCache()
        await cache.connect()

        await cache.set("boost:version", settings.APP_VERSION, expire=3600)
        await cache.set("boost:environment", settings.APP_ENV, expire=3600)

        logger.info("🔥 Cache warm-up completed successfully")
        await cache.close()

    except Exception as e:
        logger.warning(f"Cache warm-up skipped: {e}")


# -------------------------------------------------
# 🔹 Комплексная инициализация приложения
# -------------------------------------------------

async def init_app() -> None:
    """Выполняет последовательность проверок и прогрев кеша при старте."""
    await init_startup_checks()
    await warm_up_cache()


# -------------------------------------------------
# 🔹 Entrypoint (for manual startup)
# -------------------------------------------------

async def main() -> None:
    """
    Точка входа для ручного запуска проверки (python -m core.startup).
    """
    await init_startup_checks()
    await warm_up_cache()
    logger.info("🎯 Uzinex Boost core startup sequence finished.")


if __name__ == "__main__":
    asyncio.run(main())
