"""
Uzinex Boost — Cache Exceptions
===============================

Модуль определяет исключения, используемые подсистемой кэша.
Все ошибки наследуются от CacheError и могут безопасно
обрабатываться на уровне сервисов или middleware.
"""

from typing import Optional


# 🔹 Базовый класс всех ошибок кэша
class CacheError(Exception):
    """Базовый класс для всех исключений, связанных с кэшированием."""

    def __init__(self, message: str, *, key: Optional[str] = None, cause: Optional[Exception] = None):
        self.key = key
        self.cause = cause
        super().__init__(message)

    def __str__(self):
        base = super().__str__()
        if self.key:
            base += f" [key={self.key}]"
        if self.cause:
            base += f" (cause={self.cause})"
        return base


# 🔹 Ошибка подключения к Redis или недоступности бэкенда
class CacheConnectionError(CacheError):
    """Ошибка подключения или недоступности Redis."""
    pass


# 🔹 Ошибка сериализации/десериализации данных
class CacheSerializationError(CacheError):
    """Ошибка преобразования Python ↔ JSON при работе с кэшем."""
    pass


# 🔹 Превышение лимита запросов (anti-spam / rate-limit)
class RateLimitExceeded(CacheError):
    """Пользователь превысил допустимую частоту действий."""

    def __init__(self, retry_after: int, key: Optional[str] = None):
        super().__init__(f"Rate limit exceeded. Retry after {retry_after}s", key=key)
        self.retry_after = retry_after


# 🔹 Ошибка идемпотентности (повторная операция)
class IdempotencyConflict(CacheError):
    """Попытка повторного выполнения уже зарегистрированной операции."""

    def __init__(self, key: str):
        super().__init__("Duplicate idempotent operation detected", key=key)


# 🔹 Внутренняя ошибка кэша (например, неожиданный ответ Redis)
class CacheInternalError(CacheError):
    """Неожиданная ошибка при работе с Redis."""
    pass


# 🔹 Ошибка отсутствия ключа, если ожидается наличие
class CacheKeyNotFound(CacheError):
    """Ключ не найден в кэше."""
    pass


__all__ = [
    "CacheError",
    "CacheConnectionError",
    "CacheSerializationError",
    "RateLimitExceeded",
    "IdempotencyConflict",
    "CacheInternalError",
    "CacheKeyNotFound",
]
