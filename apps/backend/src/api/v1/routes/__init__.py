"""
Uzinex Boost API v1 — Routes Package
====================================

Центральный модуль маршрутов REST API (версия v1).
"""

from fastapi import APIRouter

# Импорт отдельных модулей маршрутов
from .users import router as users_router
from .payments import router as payments_router
from .balance import router as balance_router
from .telegram import router as telegram_router
from .system import router as system_router

# ----------------------------
# 🔹 Главный API роутер
# ----------------------------
router = APIRouter()

# Подключение подроутеров
router.include_router(system_router, prefix="/system", tags=["System"])
router.include_router(users_router, prefix="/users", tags=["Users"])
router.include_router(balance_router, prefix="/balance", tags=["Balance"])
router.include_router(payments_router, prefix="/payments", tags=["Payments"])
router.include_router(telegram_router, prefix="/telegram", tags=["Telegram"])

# ----------------------------
# 🔹 Экспорт
# ----------------------------
__all__ = ["router"]
