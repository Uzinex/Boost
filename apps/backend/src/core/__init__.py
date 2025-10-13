"""
Uzinex Boost — Core Package
============================

Ядро серверного приложения Boost v2.0:
- управление конфигурацией (config.py),
- безопасность и подписи (security.py),
- база данных и зависимости (database.py, deps.py),
- логирование и мониторинг (logging.py).

Этот пакет используется всеми слоями проекта:
- API (/api/v1)
- Domain (бизнес-логика)
- Adapters (инфраструктура)
- Bot (Telegram-интеграция)
"""

from __future__ import annotations

import logging as py_logging  # ✅ используем стандартное logging под другим именем
from .config import settings  # глобальная конфигурация приложения
from .logging import setup_logging  # кастомная настройка loguru / форматирование

__all__ = ["settings", "setup_logging", "__version__", "get_logger"]

# -------------------------------------------------
# 🔹 Метаданные ядра
# -------------------------------------------------

__version__ = "2.0.0"
__app_name__ = "Uzinex Boost"
__author__ = "Uzinex Engineering Team"
__license__ = "MIT"
__description__ = (
    "Uzinex Boost v2.0 — Telegram WebApp + Bot платформа "
    "для продвижения и заработка с использованием FastAPI + Aiogram."
)

# -------------------------------------------------
# 🔹 Инициализация логирования
# -------------------------------------------------

def get_logger(name: str = "uzinex.core") -> py_logging.Logger:
    """
    Возвращает преднастроенный логгер для модуля.
    Пример:
        logger = get_logger(__name__)
    """
    setup_logging()
    return py_logging.getLogger(name)


# Инициализация базового логгера при импорте ядра
setup_logging()
core_logger = get_logger("uzinex.core")
core_logger.info(f"{__app_name__} Core initialized — version {__version__}")
