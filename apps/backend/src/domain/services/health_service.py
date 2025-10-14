"""
Uzinex Boost — Health Service
=============================

Сервис системного мониторинга и проверки зависимостей приложения.

Назначение:
- Проверяет доступность основных компонентов (PostgreSQL, Redis, Telegram API);
- Используется для эндпоинта /health и внутренних диагностики;
- Может быть интегрирован с мониторингом (UptimeRobot, Grafana, etc.).
"""

from __future__ import annotations
import time
import logging
from typing import Any, Dict

import aiohttp
from sqlalchemy.ext.asyncio import AsyncEngine

from core.config import settings
from adapters.cache.redis_cache import RedisCache

logger = logging.getLogger("uzinex.domain.health")


class HealthService:
    """
    HealthService — центральный сервис проверки состояния системы.
    """

    def __init__(self, db_engine: AsyncEngine, redis_client: RedisCache):
        self.db_engine = db_engine
        self.redis_client = redis_client

    # -------------------------------------------------
    # 🔹 Проверка PostgreSQL
    # -------------------------------------------------
    async def check_postgres(self) -> bool:
        try:
            async with self.db_engine.connect() as conn:
                await conn.execute("SELECT 1")
            logger.debug("✅ PostgreSQL connection OK")
            return True
        except Exception as e:
            logger.error(f"❌ PostgreSQL check failed: {e}")
            return False

    # -------------------------------------------------
    # 🔹 Проверка Redis
    # -------------------------------------------------
    async def check_redis(self) -> bool:
        try:
            client = await self.redis_client.ensure_connection()
            pong = await client.ping()
            if pong:
                logger.debug("✅ Redis connection OK")
                return True
        except Exception as e:
            logger.error(f"❌ Redis check failed: {e}")
        return False

    # -------------------------------------------------
    # 🔹 Проверка Telegram API (опционально)
    # -------------------------------------------------
    async def check_telegram(self) -> bool:
        if not settings.TELEGRAM_BOT_TOKEN or settings.TELEGRAM_BOT_TOKEN.startswith("YOUR_"):
            logger.warning("⚠️ Telegram check skipped — bot token not configured")
            return False

        url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/getMe"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=5) as response:
                    data = await response.json()
                    if data.get("ok"):
                        logger.debug("✅ Telegram API reachable")
                        return True
                    logger.error(f"❌ Telegram API responded with error: {data}")
        except Exception as e:
            logger.error(f"❌ Telegram API check failed: {e}")
        return False

    # -------------------------------------------------
    # 🔹 Основной метод
    # -------------------------------------------------
    async def get_health_status(self) -> Dict[str, Any]:
        """
        Проверяет все ключевые сервисы и возвращает JSON-сводку.
        """
        start_time = time.perf_counter()

        postgres_ok = await self.check_postgres()
        redis_ok = await self.check_redis()
        telegram_ok = await self.check_telegram()

        elapsed = round(time.perf_counter() - start_time, 3)

        summary = {
            "status": "ok" if all([postgres_ok, redis_ok]) else "degraded",
            "details": {
                "postgres": postgres_ok,
                "redis": redis_ok,
                "telegram": telegram_ok,
            },
            "elapsed_seconds": elapsed,
            "environment": settings.APP_ENV,
            "version": settings.APP_VERSION,
        }

        logger.info(
            f"📊 Health check summary: DB={postgres_ok} | Redis={redis_ok} | Telegram={telegram_ok} | {elapsed}s"
        )
        return summary
