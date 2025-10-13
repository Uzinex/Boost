"""
Uzinex Boost Core — Logging Configuration
==========================================

Унифицированная система логирования для всех компонентов проекта:
- API (FastAPI)
- Backend (domain/adapters)
- Bot (Aiogram)
- Workers (background tasks)

Особенности:
- цветное форматирование в DEV;
- структурированные логи в PROD;
- совместимость с Railway / Docker;
- автоматическая настройка логгеров FastAPI и Uvicorn.
"""

from __future__ import annotations
import logging
import sys
import os
from datetime import datetime
from core.config import settings


# -------------------------------------------------
# 🔹 Форматтер с цветами (для DEV)
# -------------------------------------------------

class ColorFormatter(logging.Formatter):
    """Красивый цветной лог-форматтер для разработки."""

    COLORS = {
        "DEBUG": "\033[36m",     # голубой
        "INFO": "\033[32m",      # зелёный
        "WARNING": "\033[33m",   # жёлтый
        "ERROR": "\033[31m",     # красный
        "CRITICAL": "\033[41m",  # красный фон
    }

    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        level_color = self.COLORS.get(record.levelname, "")
        asctime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message = f"{asctime} | {level_color}{record.levelname:<8}{self.RESET} | {record.name}: {record.getMessage()}"
        if record.exc_info:
            message += f"\n{self.formatException(record.exc_info)}"
        return message


# -------------------------------------------------
# 🔹 Форматтер для продакшн-логов (структурированный)
# -------------------------------------------------

class JSONFormatter(logging.Formatter):
    """Структурированный формат логов для Railway / Docker (без ANSI-цветов)."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        return str(log_entry)


# -------------------------------------------------
# 🔹 Настройка логирования
# -------------------------------------------------

def setup_logging(force: bool = False) -> None:
    """
    Настраивает логирование для всего проекта.
    Автоматически вызывается при инициализации core.
    """

    # Избегаем двойной инициализации
    if logging.getLogger().handlers and not force:
        return

    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    is_dev = settings.APP_ENV.lower() in ("dev", "development")

    # Определяем форматтер
    formatter = ColorFormatter() if is_dev else JSONFormatter()

    # Поток вывода
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    # Настраиваем базовый логгер
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.handlers.clear()
    root_logger.addHandler(console_handler)

    # Настройка для FastAPI / Uvicorn
    for uvicorn_logger in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        logging.getLogger(uvicorn_logger).handlers.clear()
        logging.getLogger(uvicorn_logger).propagate = True

    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

    # Итоговое сообщение
    env = settings.APP_ENV.upper()
    root_logger.info(f"🔧 Logging configured (level={settings.LOG_LEVEL}, env={env})")


# -------------------------------------------------
# 🔹 Утилита для получения именованного логгера
# -------------------------------------------------

def get_logger(name: str = "uzinex") -> logging.Logger:
    """
    Возвращает именованный логгер.
    Пример:
        logger = get_logger("uzinex.api.system")
    """
    return logging.getLogger(name)
