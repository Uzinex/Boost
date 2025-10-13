"""
Uzinex Boost — Payments Adapter Package
=======================================

Подсистема платёжных адаптеров.

Назначение:
- взаимодействие с внешними платёжными провайдерами (Click, Payme, Apelsin, Uzcard),
- обработка ручных пополнений через чеки,
- унификация логики создания, проверки и подтверждения платежей.

Все адаптеры реализуют интерфейс PaymentProvider из base.py.
"""

from typing import Dict, Type

from .base import PaymentProvider
from .manual import ManualPaymentProvider
from .exceptions import (
    PaymentError,
    InvalidSignature,
    PaymentDeclined,
    PaymentNotFound,
    WebhookAuthError,
)
from . import utils

# Зарегистрированные платёжные провайдеры (по имени)
_REGISTERED_PROVIDERS: Dict[str, Type[PaymentProvider]] = {
    "manual": ManualPaymentProvider,
    # "click": ClickPaymentProvider,      # появится позже
    # "payme": PaymePaymentProvider,      # появится позже
    # "apelsin": ApelsinPaymentProvider,  # появится позже
    # "humo": HumoPaymentProvider,
    # "uzcard": UzcardPaymentProvider,
}


def get_provider(name: str = "manual", **kwargs) -> PaymentProvider:
    """
    Возвращает экземпляр платёжного провайдера по имени.

    :param name: идентификатор провайдера (manual, click, payme и т.д.)
    :param kwargs: параметры подключения (api_key, merchant_id и т.п.)
    :return: экземпляр PaymentProvider
    """
    name = (name or "manual").lower().strip()
    provider_cls = _REGISTERED_PROVIDERS.get(name)

    if not provider_cls:
        raise PaymentError(f"Unknown payment provider: {name}")

    return provider_cls(**kwargs)


__all__ = [
    "PaymentProvider",
    "get_provider",
    "PaymentError",
    "InvalidSignature",
    "PaymentDeclined",
    "PaymentNotFound",
    "WebhookAuthError",
    "utils",
]
