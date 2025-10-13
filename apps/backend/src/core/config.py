"""
Uzinex Boost Core — Configuration
==================================

Централизованная система конфигурации для backend ядра Boost v2.0.

Использует Pydantic BaseSettings для загрузки переменных окружения:
- API, BOT и WebApp настройки
- базы данных и Redis
- безопасность (JWT, токены, hash)
- окружение запуска (dev/staging/prod)

Поддерживает автоматическую загрузку из `.env`, Railway и Docker ENV.
"""

from __future__ import annotations

import os
from pydantic import BaseSettings, Field
from functools import lru_cache


# -------------------------------------------------
# 🔹 Settings class
# -------------------------------------------------

class Settings(BaseSettings):
    """
    Глобальные настройки приложения, доступные через `from core import settings`.
    """

    # --- 🔧 App Info ---
    APP_NAME: str = Field("Uzinex Boost", description="Название приложения")
    APP_VERSION: str = Field("2.0.0", description="Версия API")
    APP_ENV: str = Field("production", description="Окружение: development | staging | production")
    API_V1_PREFIX: str = Field("/api/v1", description="Префикс всех REST эндпоинтов")

    # --- 🌐 URLs ---
    BASE_DOMAIN: str = Field("https://boost.uzinex.com", description="Основной домен WebApp")
    BACKEND_URL: str = Field("https://api.uzinex.com", description="Базовый URL API")
    FRONTEND_URL: str = Field("https://boost.uzinex.com", description="Фронтенд (WebApp) URL")

    # --- 🗄 Database ---
    DB_HOST: str = Field("localhost", description="Хост PostgreSQL")
    DB_PORT: int = Field(5432, description="Порт PostgreSQL")
    DB_USER: str = Field("postgres", description="Имя пользователя базы данных")
    DB_PASSWORD: str = Field("postgres", description="Пароль пользователя базы данных")
    DB_NAME: str = Field("uzinex_boost", description="Имя базы данных")

    # --- ⚙️ Redis / Cache ---
    REDIS_HOST: str = Field("localhost", description="Хост Redis")
    REDIS_PORT: int = Field(6379, description="Порт Redis")
    REDIS_DB: int = Field(0, description="Номер базы Redis")
    REDIS_URL: str | None = Field(None, description="Полный URL Redis (если предоставлен)")

    # --- 🔒 Security / JWT ---
    SECRET_KEY: str = Field("CHANGE_ME_SECRET", description="Секретный ключ JWT")
    JWT_ALGORITHM: str = Field("HS256", description="Алгоритм подписи JWT")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(60 * 24 * 7, description="Срок жизни JWT токена (в минутах)")

    # --- 🤖 Telegram ---
    TELEGRAM_BOT_TOKEN: str = Field("YOUR_TELEGRAM_BOT_TOKEN", description="Токен Telegram бота")
    TELEGRAM_WEBHOOK_URL: str | None = Field(None, description="Webhook URL для Telegram API")

    # --- 💰 Currency / Business Logic ---
    UZT_TO_SUM_RATE: float = Field(75.0, description="Курс конвертации 1 UZT в сум")
    START_BONUS: float = Field(100.0, description="Бонус при регистрации (UZT)")
    REWARD_CHANNEL: float = Field(0.6, description="Вознаграждение за подписку на канал")
    REWARD_GROUP: float = Field(0.4, description="Вознаграждение за вступление в группу")

    # --- 🧠 Misc / System ---
    LOG_LEVEL: str = Field("INFO", description="Уровень логирования")
    RAILWAY_MODE: bool = Field(False, description="Флаг запуска в Railway")
    TELEGRAM_DEBUG_MODE: bool = Field(False, description="Режим отладки Telegram")
    TIMEZONE: str = Field("Asia/Tashkent", description="Часовой пояс сервера")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# -------------------------------------------------
# 🔹 Cached instance
# -------------------------------------------------

@lru_cache()
def get_settings() -> Settings:
    """Создаёт и кэширует объект настроек (singleton)."""
    return Settings()


# -------------------------------------------------
# 🔹 Удобный алиас для глобального доступа
# -------------------------------------------------

settings = get_settings()

# -------------------------------------------------
# 🔹 Derived / Computed properties
# -------------------------------------------------

# Формируем URL подключения к PostgreSQL
settings.DATABASE_URL = (
    settings.REDIS_URL
    if settings.REDIS_URL
    else f"postgresql+asyncpg://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
)

# Формируем URL Redis (если не указан)
if not settings.REDIS_URL:
    settings.REDIS_URL = f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}"
