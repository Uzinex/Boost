"""
Uzinex Boost API v1 — Payments Routes
=====================================

Эндпоинты для управления пополнениями и транзакциями.

Функционал:
- создание заявки на пополнение (manual, click, payme);
- проверка статуса операции;
- получение истории пополнений и списаний;
- интеграция с Telegram уведомлениями и UZT-балансом.

Интеграция:
использует domain.services.payments и adapters.payments
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Query, status

from domain.services.payment_service import PaymentService
from domain.services.balance_service import BalanceService
from adapters.payments import get_provider
from adapters.telegram import TelegramClient, send_notification
from core.security import get_current_user  # авторизация через Telegram WebApp

logger = logging.getLogger("uzinex.api.payments")

router = APIRouter(tags=["Payments"], prefix="/payments")


# ----------------------------
# 🔹 Вспомогательные зависимости
# ----------------------------

async def get_payment_service() -> PaymentService:
    return PaymentService()


async def get_balance_service() -> BalanceService:
    return BalanceService()


# ----------------------------
# 🔹 Создание заявки на пополнение
# ----------------------------

@router.post("/manual", response_model=Dict[str, Any])
async def create_manual_payment(
    amount: float = Query(..., gt=0, description="Сумма пополнения в UZT"),
    check_photo_url: str = Query(..., description="Ссылка на фото чека (Telegram FileID или URL)"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    payment_service: PaymentService = Depends(get_payment_service),
    telegram_client: TelegramClient = Depends(),
):
    """
    🧾 Создаёт ручную заявку на пополнение (по чеку).
    """
    try:
        provider = get_provider("manual")

        invoice = await provider.create_invoice(
            user_id=current_user["id"],
            amount_uzt=amount,
            check_photo_url=check_photo_url,
        )

        await payment_service.register_invoice(invoice)

        await send_notification(
            telegram_client,
            user_id=current_user["id"],
            text=(
                f"🧾 Ваша заявка на пополнение <b>{amount:.2f} UZT</b> создана!\n\n"
                "Ожидайте подтверждения администратором ⏳"
            ),
            message_type="info",
        )

        logger.info(f"[Payments] Manual invoice created for user {current_user['id']}, amount={amount}")
        return {"ok": True, "invoice_id": invoice.id, "status": "pending"}

    except Exception as e:
        logger.exception("[Payments] Failed to create manual payment")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# ----------------------------
# 🔹 Проверка статуса заявки
# ----------------------------

@router.get("/{invoice_id}/status", response_model=Dict[str, Any])
async def get_payment_status(
    invoice_id: str,
    payment_service: PaymentService = Depends(get_payment_service),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    📊 Проверяет статус конкретного пополнения.
    """
    try:
        invoice = await payment_service.get_invoice(invoice_id)
        if not invoice or invoice.user_id != current_user["id"]:
            raise HTTPException(status_code=404, detail="Заявка не найдена")

        return {
            "ok": True,
            "invoice_id": invoice.id,
            "status": invoice.status,
            "amount_uzt": invoice.amount_uzt,
            "created_at": str(invoice.created_at),
        }

    except Exception as e:
        logger.exception("[Payments] Failed to fetch payment status")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# ----------------------------
# 🔹 История пополнений
# ----------------------------

@router.get("/history", response_model=List[Dict[str, Any]])
async def get_payment_history(
    payment_service: PaymentService = Depends(get_payment_service),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    📜 Возвращает историю пополнений пользователя.
    """
    try:
        history = await payment_service.list_user_invoices(user_id=current_user["id"])
        return history
    except Exception as e:
        logger.exception("[Payments] Failed to fetch payment history")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# ----------------------------
# 🔹 Удаление (отмена) заявки
# ----------------------------

@router.post("/{invoice_id}/cancel", response_model=Dict[str, Any])
async def cancel_payment(
    invoice_id: str,
    payment_service: PaymentService = Depends(get_payment_service),
    telegram_client: TelegramClient = Depends(),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    ❌ Отменяет неподтверждённую заявку на пополнение.
    """
    try:
        canceled = await payment_service.cancel_invoice(invoice_id, user_id=current_user["id"])
        if not canceled:
            raise HTTPException(status_code=400, detail="Невозможно отменить — заявка уже обработана")

        await send_notification(
            telegram_client,
            user_id=current_user["id"],
            text=f"❌ Ваша заявка на пополнение #{invoice_id} отменена.",
            message_type="error",
        )

        logger.info(f"[Payments] User {current_user['id']} canceled invoice {invoice_id}")
        return {"ok": True, "invoice_id": invoice_id, "status": "canceled"}

    except Exception as e:
        logger.exception("[Payments] Failed to cancel payment")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# ----------------------------
# 🔹 Информация о курсах (UZT → SUM)
# ----------------------------

@router.get("/rates", response_model=Dict[str, Any])
async def get_exchange_rates():
    """
    💱 Возвращает текущие тарифы обмена UZT → сум.
    (пример: 1 UZT = 68 сум при оплате)
    """
    try:
        rates = {
            "UZT_to_SUM": 68,
            "SUM_to_UZT": 1 / 68,
            "min_deposit": 100,
        }
        return {"ok": True, "rates": rates}
    except Exception as e:
        logger.exception("[Payments] Failed to get exchange rates")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
