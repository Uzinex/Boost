"""
Uzinex Boost API v1 — System Routes
===================================

Служебные эндпоинты для мониторинга и диагностики состояния API.

Назначение:
- Проверка доступности API (/ping)
- Отображение версии и информации о сборке (/version)
- Проверка состояния зависимостей (/health)

Используется:
- Railway / Docker healthcheck
- Мониторинг uptime и метрик
- DevOps-алерты и CI/CD пайплайны
"""

from __future__ import annotations

import os
import time
import logging
from fastapi import APIRouter, HTTPException, status

# from domain.services.health import HealthService
from adapters.cache.redis_cache import RedisCache  # инфраструктурный слой


# -------------------------------------------------
# 🔧 Настройки и инициализация
# -------------------------------------------------

logger = logging.getLogger("uzinex.api.system")
router = APIRouter(tags=["System"], prefix="/system")

START_TIME = time.time()
VERSION = "2.0.0"
BUILD = "Uzinex Boost v2.0 — FastAPI core"
AUTHOR = "Uzinex Engineering Team"
ENV = os.getenv("APP_ENV", "production").lower()


# -------------------------------------------------
# 🔹 /ping — простейший health-check
# -------------------------------------------------

@router.get("/ping", summary="Ping API", response_model=dict)
async def ping() -> dict:
    """
    🏓 Проверяет доступность API.
    Используется Railway, Docker, CI/CD и Telegram ботом.
    """
    return {
        "ok": True,
        "service": "Uzinex Boost API",
        "message": "pong",
        "version": VERSION,
        "environment": ENV,
    }


# -------------------------------------------------
# 🔹 /version — версия и аптайм
# -------------------------------------------------

@router.get("/version", summary="Get current API version", response_model=dict)
async def get_version() -> dict:
    """
    🔖 Возвращает информацию о версии сборки, окружении и аптайме.
    """
    uptime = round(time.time() - START_TIME, 2)
    return {
        "ok": True,
        "version": VERSION,
        "build": BUILD,
        "author": AUTHOR,
        "environment": ENV,
        "uptime_seconds": uptime,
    }


# -------------------------------------------------
# 🔹 /health — системная диагностика
# -------------------------------------------------

@router.get("/health", summary="Check system dependencies", response_model=dict)
async def health_check() -> dict:
    """
    💚 Проверяет состояние ключевых зависимостей:
    - PostgreSQL (через HealthService)
    - Redis (через RedisCache)
    - Telegram (опционально)
    Возвращает детализированный отчёт для DevOps и мониторинга.
    """
    try:
        health_service = HealthService()
        redis = RedisCache()

        db_status = await health_service.check_database()
        cache_status = await redis.ping()

        uptime = round(time.time() - START_TIME, 2)
        system_ok = all([db_status, cache_status])

        logger.info(f"[System] Health check: DB={db_status}, Cache={cache_status}, Env={ENV}")

        return {
            "ok": system_ok,
            "details": {
                "database": "ok" if db_status else "fail",
                "cache": "ok" if cache_status else "fail",
            },
            "environment": ENV,
            "uptime_seconds": uptime,
        }

    except Exception as e:
        logger.exception("[System] Health check failed")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
