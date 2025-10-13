"""
Uzinex Boost API v1 — Balance Routes
====================================

Эндпоинты для работы с балансом пользователей (в UZT).

Функционал:
- получение текущего баланса;
- просмотр истории транзакций;
- (опционально) перевод между пользователями;
- синхронизация баланса с Telegram WebApp.

Интеграция:
использует domain.services.balance и Telegram уведомления.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, status, Query

from domain.services.balance import BalanceService
from domain.services.payments import PaymentService
from adapters.telegram import TelegramClient, send_notification
from core.security import get_current_user  # зависимость авторизации (WebApp initData)


logger = logging.getLogger("uzinex.api.balance")

router = APIRouter(tags=["Balance"], prefix="/balance")


# ----------------------------
# 🔹 Вспомогательные зависимости
# ----------------------------

async def get_balance_service() -> BalanceService:
    return BalanceService()


async def get_payment_service() -> PaymentService:
    return PaymentService()


# ----------------------------
# 🔹 Текущий баланс
# ----------------------------

@router.get("/", response_model=Dict[str, Any])
async def get_balance(
    current_user: Dict[str, Any] = Depends(get_current_user),
    balance_service: BalanceService = Depends(get_balance_service),
):
    """
    💰 Возвращает текущий баланс пользователя в UZT.
    """
    try:
        balance = await balance_service.get_balance(user_id=current_user["id"])
        logger.info(f"[Balance] User {current_user['id']} checked balance ({balance} UZT)")
        return {"ok": True, "balance": balance}
    except Exception as e:
        logger.exception(f"[Balance] Failed to fetch balance: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# ----------------------------
# 🔹 История транзакций
# ----------------------------

@router.get("/history", response_model=List[Dict[str, Any]])
async def get_balance_history(
    current_user: Dict[str, Any] = Depends(get_current_user),
    payment_service: PaymentService = Depends(get_payment_service),
    limit: int = Query(20, description="Максимальное количество операций"),
):
    """
    📜 Возвращает историю транзакций пользователя.
    """
    try:
        history = await payment_service.list_user_transactions(user_id=current_user["id"], limit=limit)
        return history
    except Exception as e:
        logger.exception(f"[Balance] Failed to fetch transaction history: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# ----------------------------
# 🔹 Синхронизация с Telegram WebApp
# ----------------------------

@router.post("/sync", response_model=Dict[str, Any])
async def sync_balance_with_webapp(
    telegram_client: TelegramClient = Depends(),
    current_user: Dict[str, Any] = Depends(get_current_user),
    balance_service: BalanceService = Depends(get_balance_service),
):
    """
    🔄 Синхронизирует баланс пользователя с Telegram WebApp.
    Отправляет уведомление о текущем балансе.
    """
    try:
        balance = await balance_service.get_balance(user_id=current_user["id"])

        await send_notification(
            telegram_client,
            user_id=current_user["id"],
            text=f"Ваш актуальный баланс: <b>{balance:.2f} UZT</b>",
            message_type="info",
        )

        logger.info(f"[Balance] Synced WebApp for user {current_user['id']}")
        return {"ok": True, "balance": balance}
    except Exception as e:
        logger.exception(f"[Balance] Sync error for {current_user['id']}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# ----------------------------
# 🔹 Перевод между пользователями (опционально)
# ----------------------------

@router.post("/transfer", response_model=Dict[str, Any])
async def transfer_balance(
    recipient_id: int = Query(..., description="ID получателя"),
    amount: float = Query(..., description="Сумма перевода в UZT"),
    balance_service: BalanceService = Depends(get_balance_service),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    💸 Перевод средств между пользователями.
    (будет использоваться в будущем версиях Boost).
    """
    try:
        if amount <= 0:
            raise HTTPException(status_code=400, detail="Invalid amount")

        await balance_service.transfer(
            sender_id=current_user["id"],
            recipient_id=recipient_id,
            amount_uzt=amount,
        )
        logger.info(f"[Balance] {current_user['id']} transferred {amount} UZT to {recipient_id}")
        return {"ok": True, "amount": amount, "recipient_id": recipient_id}
    except Exception as e:
        logger.exception("[Balance] Transfer failed")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
