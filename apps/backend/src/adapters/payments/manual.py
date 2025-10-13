"""
Uzinex Boost — Manual Payment Provider
======================================

Реализация базового платёжного адаптера для ручных пополнений через чеки.

Пользователь загружает фото или данные чека, админ проверяет и подтверждает.
После подтверждения баланс пополняется (узт начисляется на кошелёк).
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from datetime import datetime

from .base import PaymentProvider, PaymentInvoice
from .exceptions import (
    PaymentError,
    PaymentNotFound,
    PaymentPending,
    PaymentDeclined,
    PaymentAlreadyProcessed,
    UnsupportedOperation,
)


class ManualPaymentProvider(PaymentProvider):
    """
    Провайдер ручных пополнений (через чеки).

    Используется как fallback или дефолтный режим, если нет интеграции с API.
    """

    def __init__(self, **kwargs):
        super().__init__(name="manual")
        self._storage: Dict[str, Dict[str, Any]] = {}  # имитация локального стора (в будущем — DB записи boost_deposits)

    # ----------------------------
    # 🔹 Создание счёта (invoice)
    # ----------------------------

    async def create_invoice(self, user_id: str, amount_uzt: float, **kwargs) -> PaymentInvoice:
        """
        Создаёт заявку на пополнение (в статусе pending).
        """
        invoice_id = self.make_invoice_id()
        invoice = PaymentInvoice(
            id=invoice_id,
            user_id=user_id,
            amount_uzt=self.normalize_amount(amount_uzt),
            provider=self.name,
            status="pending",
            currency="UZS",
            pay_url=None,  # для ручного режима ссылка не требуется
            created_at=datetime.utcnow(),
            extra={"type": "manual", "note": kwargs.get("note")},
        )
        self._storage[invoice_id] = invoice.to_dict()
        return invoice

    # ----------------------------
    # 🔹 Проверка статуса оплаты
    # ----------------------------

    async def verify_payment(self, invoice_id: str, **kwargs) -> bool:
        """
        Проверяет статус оплаты (используется после модерации админом).
        """
        record = self._storage.get(invoice_id)
        if not record:
            raise PaymentNotFound("Manual invoice not found", provider=self.name, invoice_id=invoice_id)

        status = record.get("status")
        if status == "paid":
            raise PaymentAlreadyProcessed("Invoice already confirmed", provider=self.name, invoice_id=invoice_id)
        elif status == "declined":
            raise PaymentDeclined("Invoice was rejected", provider=self.name, invoice_id=invoice_id)
        elif status == "pending":
            # ожидает подтверждения админом
            raise PaymentPending("Invoice awaiting approval", provider=self.name, invoice_id=invoice_id)

        raise PaymentError(f"Unknown status: {status}", provider=self.name, invoice_id=invoice_id)

    # ----------------------------
    # 🔹 Получение статуса
    # ----------------------------

    async def get_status(self, invoice_id: str, **kwargs) -> str:
        """
        Возвращает текущий статус инвойса (pending / paid / declined).
        """
        record = self._storage.get(invoice_id)
        if not record:
            raise PaymentNotFound("Invoice not found", provider=self.name, invoice_id=invoice_id)
        return record.get("status", "unknown")

    # ----------------------------
    # 🔹 Возврат (refund)
    # ----------------------------

    async def refund(self, invoice_id: str, **kwargs) -> bool:
        """
        Возврат средств не поддерживается в ручном режиме.
        """
        raise UnsupportedOperation("Manual provider does not support refunds")

    # ----------------------------
    # 🔹 Обработка callback/webhook (для совместимости)
    # ----------------------------

    async def parse_callback(self, data: Dict[str, Any], headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Для ручного режима callback не используется.
        Метод реализован только для совместимости.
        """
        return {
            "invoice_id": data.get("invoice_id"),
            "status": data.get("status", "pending"),
            "amount_uzt": data.get("amount_uzt", 0),
            "signature_valid": True,
        }

    # ----------------------------
    # 🔹 Вспомогательные методы (для админов)
    # ----------------------------

    async def approve_invoice(self, invoice_id: str) -> bool:
        """
        Админ подтверждает оплату вручную.
        """
        record = self._storage.get(invoice_id)
        if not record:
            raise PaymentNotFound("Invoice not found", provider=self.name, invoice_id=invoice_id)

        record["status"] = "paid"
        record["confirmed_at"] = datetime.utcnow().isoformat()
        self._storage[invoice_id] = record
        return True

    async def reject_invoice(self, invoice_id: str, reason: str) -> bool:
        """
        Админ отклоняет оплату вручную (например, неверный чек).
        """
        record = self._storage.get(invoice_id)
        if not record:
            raise PaymentNotFound("Invoice not found", provider=self.name, invoice_id=invoice_id)

        record["status"] = "declined"
        record["reason"] = reason
        record["confirmed_at"] = datetime.utcnow().isoformat()
        self._storage[invoice_id] = record
        return True
