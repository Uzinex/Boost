"""
Uzinex Boost Core — Exceptions
===============================

Централизованная система обработки ошибок ядра приложения.

Назначение:
- базовый класс `AppException` для всех внутренних ошибок;
- специализированные подклассы (DBError, CacheError, AuthError и т.д.);
- интеграция с FastAPI и логированием;
- безопасная сериализация ошибок для REST API.

Используется во всех слоях: core, adapters, domain, api.
"""

from __future__ import annotations
import logging
from fastapi import HTTPException, status

logger = logging.getLogger("uzinex.core.exceptions")


# -------------------------------------------------
# 🔹 Базовое приложение-исключение
# -------------------------------------------------

class AppException(Exception):
    """
    Базовый класс для всех исключений внутри Uzinex Boost.
    Все кастомные ошибки наследуются от него.
    """

    code: int = 500
    message: str = "Internal server error"
    details: str | None = None

    def __init__(self, message: str | None = None, *, details: str | None = None, code: int | None = None):
        super().__init__(message or self.message)
        if message:
            self.message = message
        if details:
            self.details = details
        if code:
            self.code = code

        logger.error(f"[AppException] {self.message} — Details: {self.details or '-'}")

    def to_http(self) -> HTTPException:
        """
        Преобразует AppException в HTTPException для FastAPI.
        """
        return HTTPException(status_code=self.code, detail=self.message)


# -------------------------------------------------
# 🔹 Кастомные категории ошибок
# -------------------------------------------------

class AuthError(AppException):
    code = status.HTTP_401_UNAUTHORIZED
    message = "Authentication failed"


class PermissionError(AppException):
    code = status.HTTP_403_FORBIDDEN
    message = "Permission denied"


class NotFoundError(AppException):
    code = status.HTTP_404_NOT_FOUND
    message = "Requested resource not found"


class ValidationError(AppException):
    code = status.HTTP_422_UNPROCESSABLE_ENTITY
    message = "Validation error"


class DBError(AppException):
    code = status.HTTP_500_INTERNAL_SERVER_ERROR
    message = "Database operation failed"


class CacheError(AppException):
    code = status.HTTP_503_SERVICE_UNAVAILABLE
    message = "Cache system unavailable"


class TelegramAPIError(AppException):
    code = status.HTTP_502_BAD_GATEWAY
    message = "Telegram API communication failed"


class BusinessLogicError(AppException):
    code = status.HTTP_409_CONFLICT
    message = "Business rule violation"


# -------------------------------------------------
# 🔹 Утилита для глобального перехвата ошибок
# -------------------------------------------------

def handle_exception(exc: Exception) -> HTTPException:
    """
    Унифицированный обработчик ошибок, который:
    - логирует ошибку;
    - возвращает корректный HTTPException;
    - преобразует неизвестные ошибки в AppException.
    """
    if isinstance(exc, AppException):
        logger.warning(f"[Handled] {exc.__class__.__name__}: {exc.message}")
        return exc.to_http()

    if isinstance(exc, HTTPException):
        logger.warning(f"[HTTPException] {exc.detail}")
        return exc

    logger.exception(f"[Unhandled Exception] {type(exc).__name__}: {exc}")
    return HTTPException(status_code=500, detail="Internal server error")
