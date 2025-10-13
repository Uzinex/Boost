"""
Uzinex Boost API v1 — Admin Routes
==================================

Административные эндпоинты для управления системой:
- подтверждение или отклонение ручных пополнений;
- просмотр списка заявок и пользователей;
- получение статистики (общие данные по системе).

Доступ ограничен ролями (только админы).
"""

from __future__ import annotations

import logging
from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import Any, Dict, List

from domain.services.payment_service import PaymentService
from domain.services.user_service import UserService
from adapters.payments import get_provider
from adapters.telegram import send_notification, TelegramClient
from core.security import get_current_admin  # (в будущем – зависимость аутентификации)

logger = logging.getLogger("uzinex.api.admin")

router = APIRouter(tags=["Admin"], prefix="/admin")


# ----------------------------
# 🔹 Вспомогательные зависимости
# ----------------------------

async def get_payment_service() -> PaymentService:
    return PaymentService()


async def get_user_service() -> UserService:
    return UserService()


# ----------------------------
# 🔹 Подтверждение ручных платежей
# ----------------------------

@router.post("/payments/{invoice_id}/approve", response_model=Dict[str, Any])
async def approve_payment(
    invoice_id: str,
    payment_service: PaymentService = Depends(get_payment_service),
    telegram_client: TelegramClient = Depends(),
    current_admin: Dict[str, Any] = Depends(get_current_admin),
):
    """
    ✅ Подтверждает ручное пополнение (админом).
    """
    provider = get_provider("manual")
    try:
        await provider.approve_invoice(invoice_id)
        await payment_service.confirm_payment(invoice_id)

        # Отправляем уведомление пользователю
        invoice = await payment_service.get_invoice(invoice_id)
        await send_notification(
            telegram_client,
            user_id=invoice.user_id,
            text=f"Ваше пополнение на {invoice.amount_uzt:.2f} UZT подтверждено ✅",
            message_type="success",
        )

        logger.info(f"[Admin] Payment {invoice_id} approved by {current_admin['username']}")
        return {"ok": True, "invoice_id": invoice_id, "status": "paid"}

    except Exception as e:
        logger.exception(f"[Admin] Failed to approve invoice {invoice_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/payments/{invoice_id}/reject", response_model=Dict[str, Any])
async def reject_payment(
    invoice_id: str,
    reason: str = Query(..., description="Причина отклонения"),
    payment_service: PaymentService = Depends(get_payment_service),
    telegram_client: TelegramClient = Depends(),
    current_admin: Dict[str, Any] = Depends(get_current_admin),
):
    """
    ❌ Отклоняет ручное пополнение (админом).
    """
    provider = get_provider("manual")
    try:
        await provider.reject_invoice(invoice_id, reason)
        await payment_service.decline_payment(invoice_id, reason)

        invoice = await payment_service.get_invoice(invoice_id)
        await send_notification(
            telegram_client,
            user_id=invoice.user_id,
            text=f"Ваше пополнение отклонено ❌\nПричина: {reason}",
            message_type="error",
        )

        logger.info(f"[Admin] Payment {invoice_id} rejected by {current_admin['username']}")
        return {"ok": True, "invoice_id": invoice_id, "status": "declined", "reason": reason}

    except Exception as e:
        logger.exception(f"[Admin] Failed to reject invoice {invoice_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# ----------------------------
# 🔹 Управление пользователями
# ----------------------------

@router.get("/users", response_model=List[Dict[str, Any]])
async def list_users(
    user_service: UserService = Depends(get_user_service),
    current_admin: Dict[str, Any] = Depends(get_current_admin),
):
    """
    👤 Получить список всех пользователей (для админ-панели).
    """
    try:
        users = await user_service.list_all()
        logger.info(f"[Admin] {current_admin['username']} fetched user list.")
        return users
    except Exception as e:
        logger.exception("[Admin] Failed to fetch users")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# ----------------------------
# 🔹 Системная статистика
# ----------------------------

@router.get("/stats", response_model=Dict[str, Any])
async def get_system_stats(
    payment_service: PaymentService = Depends(get_payment_service),
    user_service: UserService = Depends(get_user_service),
    current_admin: Dict[str, Any] = Depends(get_current_admin),
):
    """
    📊 Получить общую статистику по системе.
    """
    try:
        stats = {
            "total_users": await user_service.count_users(),
            "total_payments": await payment_service.count_all(),
            "total_volume_uzt": await payment_service.get_total_volume(),
        }
        logger.info(f"[Admin] {current_admin['username']} fetched system stats.")
        return stats
    except Exception as e:
        logger.exception("[Admin] Failed to fetch system stats")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
