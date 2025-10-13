"""
Uzinex Boost — Payment Exceptions
=================================

Единый модуль исключений для платёжных адаптеров.

Используется для унифицированной обработки ошибок при работе
с внешними платёжными системами (Click, Payme, Uzcard и др.).
"""

from typing import Optional


# ----------------------------
# 🔹 Базовый класс
# ----------------------------

class PaymentError(Exception):
    """Базовый класс всех ошибок, связанных с платежами."""

    def __init__(self, message: str, *, provider: Optional[str] = None, invoice_id: Optional[str] = None):
        self.provider = provider
        self.invoice_id = invoice_id
        super().__init__(message)

    def __str__(self) -> str:
        base = super().__str__()
        if self.provider:
            base += f" [provider={self.provider}]"
        if self.invoice_id:
            base += f" [invoice={self.invoice_id}]"
        return base


# ----------------------------
# 🔹 Специализированные ошибки
# ----------------------------

class PaymentNotFound(PaymentError):
    """Платёж или счёт не найден в системе провайдера."""
    pass


class InvalidSignature(PaymentError):
    """Ошибка верификации подписи webhook или callback."""
    pass


class PaymentDeclined(PaymentError):
    """Платёж был отклонён (пользователь отменил, недостаточно средств и т.п.)."""
    pass


class PaymentPending(PaymentError):
    """Платёж находится в ожидании, ещё не подтверждён."""
    pass


class PaymentAlreadyProcessed(PaymentError):
    """Платёж уже обработан и не может быть повторно подтверждён."""
    pass


class PaymentTimeout(PaymentError):
    """Платёж не подтверждён в установленный срок."""
    pass


class PaymentConnectionError(PaymentError):
    """Ошибка сети или недоступность API провайдера."""
    pass


class WebhookAuthError(PaymentError):
    """Ошибка авторизации при приёме webhook от провайдера."""
    pass


class UnsupportedOperation(PaymentError):
    """Метод или действие не поддерживается данным провайдером."""
    pass


# ----------------------------
# 🔹 Экспорт
# ----------------------------

__all__ = [
    "PaymentError",
    "PaymentNotFound",
    "InvalidSignature",
    "PaymentDeclined",
    "PaymentPending",
    "PaymentAlreadyProcessed",
    "PaymentTimeout",
    "PaymentConnectionError",
    "WebhookAuthError",
    "UnsupportedOperation",
]
