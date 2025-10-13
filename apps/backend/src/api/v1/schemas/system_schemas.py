"""
Uzinex Boost API v1 — System Schemas
=====================================

Служебные схемы данных, используемые для мониторинга, диагностики
и версионирования API (эндпоинты /system/*).

Назначение:
- /system/ping — проверка доступности API;
- /system/version — версия и аптайм;
- /system/health — проверка зависимостей (DB, Redis, Telegram).
"""

from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Optional


# -------------------------------------------------
# 🔹 Ping
# -------------------------------------------------

class PingResponse(BaseModel):
    """Ответ для эндпоинта /system/ping."""
    ok: bool = Field(True, description="Статус API")
    service: str = Field("Uzinex Boost API", description="Название сервиса")
    message: str = Field("pong", description="Ответ API на ping")
    version: str = Field("2.0.0", description="Текущая версия API")
    environment: str = Field("production", description="Текущее окружение")

    class Config:
        json_schema_extra = {
            "example": {
                "ok": True,
                "service": "Uzinex Boost API",
                "message": "pong",
                "version": "2.0.0",
                "environment": "production"
            }
        }


# -------------------------------------------------
# 🔹 Version
# -------------------------------------------------

class VersionResponse(BaseModel):
    """Ответ с информацией о версии API."""
    ok: bool = Field(True, description="Статус API")
    version: str = Field(..., description="Версия сборки API")
    build: str = Field(..., description="Название или хэш сборки")
    author: str = Field("Uzinex Engineering Team", description="Автор или команда разработки")
    environment: str = Field(..., description="Окружение API (production/staging/dev)")
    uptime_seconds: float = Field(..., description="Время работы API в секундах")

    class Config:
        json_schema_extra = {
            "example": {
                "ok": True,
                "version": "2.0.0",
                "build": "Uzinex Boost v2.0 — FastAPI core",
                "author": "Uzinex Engineering Team",
                "environment": "production",
                "uptime_seconds": 412.55
            }
        }


# -------------------------------------------------
# 🔹 Health
# -------------------------------------------------

class HealthDetails(BaseModel):
    """Подробные данные о состоянии компонентов системы."""
    database: str = Field(..., description="Статус подключения к PostgreSQL (ok/fail)")
    cache: str = Field(..., description="Статус Redis (ok/fail)")
    telegram: Optional[str] = Field(None, description="Статус Telegram API (ok/fail)")

    class Config:
        json_schema_extra = {
            "example": {
                "database": "ok",
                "cache": "ok",
                "telegram": "ok"
            }
        }


class HealthResponse(BaseModel):
    """Ответ для эндпоинта /system/health."""
    ok: bool = Field(..., description="Общий статус системы (True, если все сервисы в порядке)")
    details: HealthDetails = Field(..., description="Подробности по подсистемам")
    environment: str = Field("production", description="Текущее окружение")
    uptime_seconds: float = Field(..., description="Аптайм системы в секундах")

    class Config:
        json_schema_extra = {
            "example": {
                "ok": True,
                "details": {
                    "database": "ok",
                    "cache": "ok",
                    "telegram": "ok"
                },
                "environment": "production",
                "uptime_seconds": 784.23
            }
        }
