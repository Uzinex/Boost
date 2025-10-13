"""
Uzinex Boost — Payment Provider Base
====================================

Абстрактный слой платёжных адаптеров.

Каждый провайдер должен реализовать интерфейс PaymentProvider:
- create_invoice() — создание платежа/счёта
- verify_payment() — проверка статуса оплаты
- get_status() — получение текущего состояния транзакции
- refund() — возврат средств (если поддерживается)
- parse_callback() — разбор входящих webhook-уведомлений (если провайдер их шлёт)

Используется в сервисе DepositService.
"""

from __future__ import annotations

import abc
import uuid
from typing import Any, Dict, Optional, Union
from datetime import datetime


class PaymentInvoice:
    """
    Универсальная модель счёта (invoice), возвращаемая провайдерами.
    """

    def __init__(
        self,
        id: Union[str, uuid.UUID],
        user_id: str,
        amount_uzt: float,
        provider: str,
        currency: str = "UZS",
        status: str = "pending",
        pay_url: Optional[str] = None,
        created_at: Optional[datetime] = None,
        extra: Optional[Dict[str, Any]] = None,
    ):
        self.id = str(id)
        self.user_id = user_id
        self.amount_uzt = float(amount_uzt)
        self.provider = provider
        self.currency = currency
        self.status = status
        self.pay_url = pay_url
        self.created_at = created_at or datetime.utcnow()
        self.extra = extra or {}

    def to_dict(self) -> Dict[str, Any]:
        """Преобразует объект в словарь (для JSON или ответа API)."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "amount_uzt": self.amount_uzt,
            "provider": self.provider,
            "currency": self.currency,
            "status": self.status,
            "pay_url": self.pay_url,
            "created_at": self.created_at.isoformat(),
            "extra": self.extra,
        }

    def __repr__(self) -> str:
        return f"<PaymentInvoice id={self.id} provider={self.provider} status={self.status}>"


class PaymentProvider(abc.ABC):
    """
    Абстрактный базовый класс платёжных провайдеров.
    """

    def __init__(
        self,
        name: str,
        merchant_id: Optional[str] = None,
        api_key: Optional[str] = None,
        secret: Optional[str] = None,
        sandbox: bool = False,
    ):
        self.name = name
        self.merchant_id = merchant_id
        self.api_key = api_key
        self.secret = secret
        self.sandbox = sandbox

    # ----------------------------
    # 🔹 Основные операции
    # ----------------------------

    @abc.abstractmethod
    async def create_invoice(self, user_id: str, amount_uzt: float, **kwargs) -> PaymentInvoice:
        """
        Создаёт новый счёт (invoice) на оплату.

        Возвращает объект PaymentInvoice с pay_url (если применимо).
        """
        raise NotImplementedError

    @abc.abstractmethod
    async def verify_payment(self, invoice_id: str, **kwargs) -> bool:
        """
        Проверяет статус оплаты по invoice_id.
        Возвращает True, если платёж подтверждён.
        """
        raise NotImplementedError

    @abc.abstractmethod
    async def get_status(self, invoice_id: str, **kwargs) -> str:
        """
        Возвращает текущий статус платежа:
        'pending', 'paid', 'failed', 'refunded', 'expired' и т.п.
        """
        raise NotImplementedError

    @abc.abstractmethod
    async def refund(self, invoice_id: str, **kwargs) -> bool:
        """
        Выполняет возврат средств (если провайдер поддерживает).
        Возвращает True, если успешно.
        """
        raise NotImplementedError

    @abc.abstractmethod
    async def parse_callback(self, data: Dict[str, Any], headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Разбирает и валидирует webhook/callback от провайдера.
        Возвращает нормализованный dict:
        {
            "invoice_id": str,
            "status": str,
            "amount_uzt": float,
            "signature_valid": bool
        }
        """
        raise NotImplementedError

    # ----------------------------
    # 🔹 Вспомогательные методы
    # ----------------------------

    def make_invoice_id(self) -> str:
        """Генерирует UUID для внутреннего счёта."""
        return str(uuid.uuid4())

    def normalize_amount(self, value: Union[int, float, str]) -> float:
        """Безопасно приводит сумму к float."""
        try:
            return round(float(value), 2)
        except Exception:
            return 0.0

    def now(self) -> datetime:
        """Текущее UTC-время."""
        return datetime.utcnow()
