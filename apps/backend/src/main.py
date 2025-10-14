from __future__ import annotations

"""
Uzinex Boost — Main Application Entry Point
===========================================

Главный модуль запуска backend-системы Uzinex Boost v2.0.

Назначение:
-----------
- инициализация FastAPI-приложения;
- регистрация маршрутов API (v1);
- подключение middlewares (CORS, Logging);
- события старта и завершения приложения;
- интеграция с базой данных, Redis и Telegram Bot.

Запуск:
--------
$ uvicorn apps.backend.src.main:app --reload
"""

# -------------------------------------------------
# 🔹 Импорт стандартных зависимостей
# -------------------------------------------------
import os
import sys
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

# -------------------------------------------------
# 🔹 Добавляем путь к Telegram Bot
# -------------------------------------------------
BOT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../bot"))
if BOT_PATH not in sys.path:
    sys.path.append(BOT_PATH)

try:
    from bot.app.service.bot_service import *  # основной модуль бота
    logger.info("🤖 Telegram Bot module loaded successfully.")
except Exception as e:
    logger.warning(f"⚠️ Telegram Bot module not loaded: {e}")

# -------------------------------------------------
# 🔹 Импорты ядра приложения
# -------------------------------------------------
from core.config import settings
from core.database import engine
from core.startup import init_app
from core.logging import setup_logging
from db.base import Base

# -------------------------------------------------
# 🔹 Инициализация FastAPI
# -------------------------------------------------
app = FastAPI(
    title="Uzinex Boost API",
    version="2.0.0",
    description="High-performance backend for Uzinex Boost v2.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# -------------------------------------------------
# 🔹 CORS Middleware
# -------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------------------
# 🔹 Логирование и стартовое сообщение
# -------------------------------------------------
setup_logging()
logger.info("🚀 Starting Uzinex Boost API v2.0...")

# -------------------------------------------------
# 🔹 Подключение маршрутов
# -------------------------------------------------
try:
    from api.v1.routes import router as api_router
    app.include_router(api_router, prefix="/api/v1")
    logger.info("✅ API routes successfully registered.")
except ImportError as e:
    logger.warning(f"⚠️ API routes not loaded: {e}")

# -------------------------------------------------
# 🔹 События приложения
# -------------------------------------------------
@app.on_event("startup")
async def on_startup():
    """Выполняется при запуске приложения."""
    logger.info("🔧 Initializing Uzinex Boost backend components...")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    await init_app()
    logger.success("✅ Application startup completed.")


@app.on_event("shutdown")
async def on_shutdown():
    """Выполняется при завершении приложения."""
    logger.info("🧹 Shutting down Uzinex Boost backend...")
    await asyncio.sleep(0.1)
    logger.success("🛑 Application stopped gracefully.")

# -------------------------------------------------
# 🔹 Корневой маршрут (Healthcheck)
# -------------------------------------------------
@app.get("/", tags=["System"])
async def root():
    """Healthcheck: Проверка состояния API."""
    return {
        "status": "ok",
        "service": "Uzinex Boost Backend",
        "version": "2.0.0",
        "environment": settings.APP_ENV,
    }
