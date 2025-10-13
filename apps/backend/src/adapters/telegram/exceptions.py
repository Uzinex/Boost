"""
Uzinex Boost — Telegram Exceptions
==================================

Модуль определяет исключения, возникающие при взаимодействии с Telegram API,
проверке WebApp initData и обработке webhook-запросов.
"""


# ----------------------------
# 🔹 Базовый класс
# ----------------------------

class TelegramError(Exception):
    """Базовый класс для всех Telegram-исключений."""

    def __init__(self, message: str, *, cause: Exception | None = None):
        self.cause = cause
        super().__init__(message)

    def __str__(self) -> str:
        base = super().__str__()
        if self.cause:
            base += f" (cause={self.cause})"
        return base


# ----------------------------
# 🔹 Ошибки API
# ----------------------------

class TelegramAPIError(TelegramError):
    """Ошибка при вызове Telegram Bot API."""
    pass


class TelegramRequestError(TelegramAPIError):
    """Ошибка HTTP-запроса или недоступность Telegram API."""
    pass


class TelegramResponseError(TelegramAPIError):
    """Telegram вернул некорректный ответ."""
    pass


# ----------------------------
# 🔹 Ошибки WebApp авторизации
# ----------------------------

class InvalidInitData(TelegramError):
    """Некорректные или поддельные данные Telegram WebApp initData."""
    pass


class ExpiredInitData(TelegramError):
    """initData устарела (превышен допустимый auth_date)."""
    pass


# ----------------------------
# 🔹 Ошибки Webhook / безопасности
# ----------------------------

class WebhookUnauthorized(TelegramError):
    """Неавторизованный webhook-запрос от Telegram."""
    pass


class WebhookProcessingError(TelegramError):
    """Ошибка при разборе webhook-запроса."""
    pass


# ----------------------------
# 🔹 Прочее
# ----------------------------

class TelegramUserNotFound(TelegramError):
    """Пользователь не найден или недоступен."""
    pass


class TelegramMessageError(TelegramError):
    """Ошибка при отправке сообщения пользователю."""
    pass


# ----------------------------
# 🔹 Экспорт
# ----------------------------

__all__ = [
    "TelegramError",
    "TelegramAPIError",
    "TelegramRequestError",
    "TelegramResponseError",
    "InvalidInitData",
    "ExpiredInitData",
    "WebhookUnauthorized",
    "WebhookProcessingError",
    "TelegramUserNotFound",
    "TelegramMessageError",
]
