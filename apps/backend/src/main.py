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
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from loguru import logger

# -------------------------------------------------
# 🔹 Настройка путей (универсально для Railway и локали)
# -------------------------------------------------
BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_ROOT not in sys.path:
    sys.path.append(BACKEND_ROOT)

BOT_PATH = os.path.join(BACKEND_ROOT, "bot")
if BOT_PATH not in sys.path:
    sys.path.append(BOT_PATH)

WEBAPP_DIR = Path(BACKEND_ROOT) / "bot" / "webapp"

WEBAPP_PUBLIC = WEBAPP_DIR / "public"
WEBAPP_SRC = WEBAPP_DIR / "src"

# -------------------------------------------------
# 🔹 Попытка импортировать Telegram Bot
# -------------------------------------------------
try:
    from bot.app.service.bot_service import *  # type: ignore
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
# 🔹 Инициализация FastAPI-приложения
# -------------------------------------------------
app = FastAPI(
    title="Uzinex Boost API",
    version="2.0.0",
    description="High-performance backend for Uzinex Boost v2.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

if WEBAPP_SRC.exists():
    app.mount("/src", StaticFiles(directory=WEBAPP_SRC), name="webapp-src")


styles_dir = WEBAPP_PUBLIC / "styles"
if styles_dir.exists():
    app.mount("/styles", StaticFiles(directory=styles_dir), name="webapp-styles")

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
# 🔹 Логирование и запуск
# -------------------------------------------------
setup_logging()
logger.info("🚀 Starting Uzinex Boost API v2.0...")

# -------------------------------------------------
# 🔹 Подключение маршрутов API
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
# 🔹 Healthcheck Endpoint
# -------------------------------------------------
@app.get("/", include_in_schema=False)
async def serve_webapp():
    """Возвращает собранный Telegram WebApp или healthcheck JSON, если сборки нет."""
    build_index = WEBAPP_PUBLIC / "index.html"
    dev_index = WEBAPP_DIR / "index.html"

    if build_index.exists():
        logger.debug("📄 Serving built webapp index.html")
        return FileResponse(build_index)

    if dev_index.exists():
        logger.debug("🛠️ Serving development webapp index.html")
        return FileResponse(dev_index)

    logger.warning("⚠️ WebApp index not found, falling back to JSON healthcheck.")
    return {
        "status": "ok",
        "service": "Uzinex Boost Backend",
        "version": "2.0.0",
        "environment": settings.APP_ENV,
    }


@app.get("/manifest.webmanifest", include_in_schema=False)
async def serve_manifest():
    manifest_path = WEBAPP_PUBLIC / "manifest.webmanifest"
    if manifest_path.exists():
        logger.debug("🧾 Serving manifest.webmanifest")
        return FileResponse(manifest_path, media_type="application/manifest+json")

    raise HTTPException(status_code=404, detail="manifest.webmanifest not found")


@app.get("/favicon.svg", include_in_schema=False)
async def serve_favicon():
    favicon_path = WEBAPP_PUBLIC / "favicon.svg"
    if favicon_path.exists():
        logger.debug("🖼️ Serving favicon.svg")
        return FileResponse(favicon_path, media_type="image/svg+xml")

    raise HTTPException(status_code=404, detail="favicon.svg not found")


@app.get("/healthz", tags=["System"])
async def healthcheck():
    """Healthcheck endpoint for deployment probes."""
    return {
        "status": "ok",
        "service": "Uzinex Boost Backend",
        "version": "2.0.0",
        "environment": settings.APP_ENV,
    }

# -------------------------------------------------
# 🔹 Автозапуск Telegram Bot при старте backend
# -------------------------------------------------
@app.on_event("startup")
async def start_bot_on_backend():
    """Запускает Telegram-бота параллельно с backend (Aiogram v3)."""
    import asyncio
    from bot import dp, bot  # Убедись, что в bot/__init__.py есть bot = Bot(...)

    async def run_bot():
        await asyncio.sleep(2)  # ждём, пока API и Redis поднимутся
        logger.info("🤖 Launching Telegram bot polling (Aiogram 3)...")
        try:
            await dp.start_polling(bot)
        except Exception as e:
            logger.error(f"❌ Telegram bot polling stopped: {e}")

    asyncio.create_task(run_bot())


