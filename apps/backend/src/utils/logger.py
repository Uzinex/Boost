"""
Uzinex Boost — Logger Utilities
===============================

Расширенные инструменты логирования для системы Uzinex Boost v2.0.

Назначение:
-----------
Предоставляет функции и настройки для форматирования логов в dev/prod средах:
- цветной и минималистичный вывод в консоль (для разработчиков);
- JSON-формат логов (для production);
- контекстное логирование (user_id, service, request_id);
- контроль уровня логирования.

Используется в:
- core.logging
- domain.services.*
- api.v1.middleware
"""

from __future__ import annotations
import json
import sys
from loguru import logger
from datetime import datetime
from typing import Any, Optional, Dict

# -------------------------------------------------
# 🔹 Настройки по умолчанию
# -------------------------------------------------
LOG_LEVEL = "INFO"
LOG_FORMAT_DEV = (
    "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> — "
    "<white>{message}</white>"
)

# JSON-формат (для production / аналитики)
def json_formatter(record: Dict[str, Any]) -> str:
    log = {
        "timestamp": record["time"].strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        "level": record["level"].name,
        "message": record["message"],
        "module": record["name"],
        "function": record["function"],
        "line": record["line"],
    }
    if record["extra"]:
        log["context"] = record["extra"]
    return json.dumps(log, ensure_ascii=False)


# -------------------------------------------------
# 🔹 Инициализация логирования
# -------------------------------------------------
def init_logger(environment: str = "development"):
    """
    Инициализирует логгер в зависимости от среды.
    """
    logger.remove()  # убираем стандартный handler

    if environment == "production":
        logger.add(sys.stdout, level=LOG_LEVEL, serialize=True, format=json_formatter)
    else:
        logger.add(sys.stdout, colorize=True, format=LOG_FORMAT_DEV, level=LOG_LEVEL)

    logger.info(f"Logger initialized for {environment.upper()} environment")


# -------------------------------------------------
# 🔹 Контекстное логирование
# -------------------------------------------------
def with_context(**kwargs):
    """
    Привязывает контекст к логгеру.
    Пример:
        log = with_context(user_id=42, service="balance")
        log.info("Баланс обновлён")
    """
    return logger.bind(**kwargs)


# -------------------------------------------------
# 🔹 Упрощённые функции логирования
# -------------------------------------------------
def log_info(message: str, **kwargs):
    """Инфо-лог с контекстом."""
    with_context(**kwargs).info(message)


def log_warning(message: str, **kwargs):
    """Предупреждение."""
    with_context(**kwargs).warning(message)


def log_error(message: str, **kwargs):
    """Ошибка."""
    with_context(**kwargs).error(message)


def log_debug(message: str, **kwargs):
    """Отладочный лог."""
    with_context(**kwargs).debug(message)
