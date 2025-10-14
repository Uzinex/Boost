"""
Uzinex Boost API v1 — System Routes
===================================

Health-check endpoints для мониторинга системы.
"""

from __future__ import annotations
import time
import logging
from fastapi import APIRouter, HTTPException, status

from adapters.cache.redis_cache import RedisCache
from adapters.telegram.client import TelegramClient
from core.config import settings
from domain.services.health_service import HealthService

logger = logging.getLogger("uzinex.api.system")
router = APIRouter(tags=["System"], prefix="/system")

START_TIME = time.time()


@router.get("/ping", summary="Ping API")
async def ping() -> dict:
    """Простой healthcheck."""
    return {
        "ok": True,
        "message": "pong",
        "service": "Uzinex Boost API",
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENV,
    }


@router.get("/health", summary="Check all system components")
async def health() -> dict:
    """Полный healthcheck (DB, Redis, Telegram)."""
    try:
        db = await HealthService().check_database()
        cache = await RedisCache().ping()

        tg_ok = False
        try:
            tg = TelegramClient(settings.TELEGRAM_BOT_TOKEN)
            me = await tg.get_me()
            tg_ok = bool(me and me.username)
        except Exception as e:
            logger.warning(f"Telegram healthcheck failed: {e}")

        uptime = round(time.time() - START_TIME, 2)
        overall_ok = all([db, cache, tg_ok])

        return {
            "ok": overall_ok,
            "components": {
                "database": db,
                "redis": cache,
                "telegram": tg_ok,
            },
            "version": settings.APP_VERSION,
            "environment": settings.APP_ENV,
            "uptime_seconds": uptime,
        }

    except Exception as e:
        logger.exception("System healthcheck failed")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
