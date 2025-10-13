"""
Uzinex Boost API v1 — Routes Package
====================================

Центральный модуль маршрутов REST API (версия v1).

Назначение:
- объединяет все подроутеры (users, payments, balance, telegram, system);
- задаёт единое префиксное пространство /api/v1/;
- используется при инициализации FastAPI-приложения.

Пример подключения:
    from api.v1.routes import api_router
    app.include_router(api_router, prefix="/api/v1")
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

api_router = APIRouter()

# Подключение подроутеров
api_router.include_router(system_router, prefix="/system", tags=["System"])
api_router.include_router(users_router, prefix="/users", tags=["Users"])
api_router.include_router(balance_router, prefix="/balance", tags=["Balance"])
api_router.include_router(payments_router, prefix="/payments", tags=["Payments"])
api_router.include_router(telegram_router, prefix="/telegram", tags=["Telegram"])

# ----------------------------
# 🔹 Экспорт
# ----------------------------

__all__ = ["api_router"]
