"""
Uzinex Boost — Exception Utilities
==================================

Унифицированная система кастомных исключений для backend-платформы Uzinex Boost v2.0.

Назначение:
-----------
Определяет собственные классы ошибок, которые обеспечивают:
- единый формат сообщений в API и логах;
- контроль бизнес-ошибок (валидация, доступ, конфликты);
- отслеживание источников проблем при отладке.

Используется в:
- domain.services.*
- core.security
- api.v1.error_handlers
- db.repositories.*
"""

from typing import Any, Optional
from fastapi import status


# -------------------------------------------------
# 🔹 Базовый класс исключений
# -------------------------------------------------
class UzinexError(Exception):
    """
    Базовый класс для всех ошибок системы Uzinex.
    Содержит код статуса, человеко-читаемое сообщение и метаданные.
    """

    def __init__(self, message: str, status_code: int = status.HTTP_400_BAD_REQUEST, details: Optional[Any] = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details or {}

    def to_dict(self) -> dict:
        """
        Преобразует ошибку в формат словаря для API-ответа.
        """
        return {
            "error": self.__class__.__name__,
            "message": self.message,
            "status": self.status_code,
            "details": self.details,
        }

    def __str__(self) -> str:
        return f"[{self.__class__.__name__}] {self.message}"


# -------------------------------------------------
# 🔹 Ошибки валидации и данных
# -------------------------------------------------
class ValidationError(UzinexError):
    """Ошибка валидации пользовательских данных."""

    def __init__(self, message: str = "Validation failed", details: Optional[Any] = None):
        super().__init__(message, status.HTTP_422_UNPROCESSABLE_ENTITY, details)


class NotFoundError(UzinexError):
    """Ошибка: объект не найден."""

    def __init__(self, message: str = "Object not found", details: Optional[Any] = None):
        super().__init__(message, status.HTTP_404_NOT_FOUND, details)


class ConflictError(UzinexError):
    """Ошибка: конфликт данных (например, дублирование)."""

    def __init__(self, message: str = "Conflict detected", details: Optional[Any] = None):
        super().__init__(message, status.HTTP_409_CONFLICT, details)


# -------------------------------------------------
# 🔹 Ошибки безопасности и доступа
# -------------------------------------------------
class AccessDenied(UzinexError):
    """Ошибка: недостаточно прав для выполнения действия."""

    def __init__(self, message: str = "Access denied", details: Optional[Any] = None):
        super().__init__(message, status.HTTP_403_FORBIDDEN, details)


class AuthenticationError(UzinexError):
    """Ошибка: неверные учетные данные или истёкший токен."""

    def __init__(self, message: str = "Authentication failed", details: Optional[Any] = None):
        super().__init__(message, status.HTTP_401_UNAUTHORIZED, details)


# -------------------------------------------------
# 🔹 Ошибки системы и сервера
# -------------------------------------------------
class InternalError(UzinexError):
    """Ошибка сервера (внутренняя)."""

    def __init__(self, message: str = "Internal server error", details: Optional[Any] = None):
        super().__init__(message, status.HTTP_500_INTERNAL_SERVER_ERROR, details)


class ServiceUnavailable(UzinexError):
    """Ошибка: внешний сервис недоступен (например, платёжный шлюз)."""

    def __init__(self, message: str = "Service temporarily unavailable", details: Optional[Any] = None):
        super().__init__(message, status.HTTP_503_SERVICE_UNAVAILABLE, details)
