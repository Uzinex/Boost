"""
Uzinex Boost — Application Startup Module
=========================================

Инициализация инфраструктурных компонентов приложения:
- PostgreSQL
- Redis
- Telegram (опционально)
"""

from __future__ import annotations
import time
import logging
from core.config import settings
from core.database import test_database_connection
from adapters.cache.redis_cache import RedisCache

logger = logging.getLogger("uzinex.core.startup")

redis_cache: RedisCache | None = None


async def init_app():
    """Запускает все инфраструктурные проверки при старте FastAPI-приложения."""
    global redis_cache

    logger.info("🚀 Starting Uzinex Boost initialization sequence...")
    start_time = time.perf_counter()

    # -----------------------------
    # 🔹 Проверка PostgreSQL
    # -----------------------------
    db_ok = await test_database_connection()
    if db_ok:
        logger.info("🗄 PostgreSQL connection: ✅ OK")
    else:
        logger.error("❌ PostgreSQL connection: FAIL")

    # -----------------------------
    # 🔹 Подключение Redis
    # -----------------------------
    redis_ok = False
    try:
        redis_cache = RedisCache(url=settings.REDIS_URL)
        await redis_cache.connect()
        redis_ok = True
    except Exception as e:
        logger.error(f"Redis initialization failed: {e}")

    logger.info(f"🧠 Redis connection: {'✅ OK' if redis_ok else '❌ FAIL'}")

    # -----------------------------
    # 🔹 Telegram (опционально)
    # -----------------------------
    telegram_ok = None  # пока не реализовано

    # -----------------------------
    # 🔹 Финальная сводка
    # -----------------------------
    elapsed = time.perf_counter() - start_time
    logger.info(f"✅ Startup checks completed in {elapsed:.2f}s")
    logger.info(f"System summary → DB: {db_ok} | Redis: {redis_ok} | Telegram: {telegram_ok}")

    if not db_ok or not redis_ok:
        logger.warning("⚠️ Some dependencies failed — application may not work correctly!")

    # -----------------------------
    # 🔹 Cache warm-up
    # -----------------------------
    if redis_ok:
        try:
            await redis_cache.set("system:startup_check", "ok", expire=30)
        except Exception as e:
            logger.warning(f"Cache warm-up failed: {e}")
    else:
        logger.warning("Cache warm-up skipped: Redis unavailable.")
