"""
Uzinex Boost API v1 — Orders Routes
===================================

Эндпоинты для работы с заказами (накрутки, продвижение).

Функционал:
- создание нового заказа;
- получение списка заказов пользователя;
- просмотр деталей и статуса заказа;
- отмена или завершение заказа;
- автоматическое списание UZT при создании.

Интеграция:
использует domain.services.orders и баланс UZT.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, status, Query

from domain.services.orders import OrderService
from domain.services.balance import BalanceService
from adapters.telegram import TelegramClient, send_notification
from core.security import get_current_user  # авторизация через Telegram WebApp

logger = logging.getLogger("uzinex.api.orders")

router = APIRouter(tags=["Orders"], prefix="/orders")


# ----------------------------
# 🔹 Вспомогательные зависимости
# ----------------------------

async def get_order_service() -> OrderService:
    return OrderService()


async def get_balance_service() -> BalanceService:
    return BalanceService()


# ----------------------------
# 🔹 Создание заказа
# ----------------------------

@router.post("/", response_model=Dict[str, Any])
async def create_order(
    order_type: str = Query(..., description="Тип заказа: channel | group"),
    target_url: str = Query(..., description="Ссылка на канал или группу"),
    quantity: int = Query(..., ge=10, le=10000, description="Количество участников/подписок"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    order_service: OrderService = Depends(get_order_service),
    balance_service: BalanceService = Depends(get_balance_service),
    telegram_client: TelegramClient = Depends(),
):
    """
    ➕ Создаёт новый заказ на продвижение.
    Списывает UZT с баланса пользователя.
    """
    try:
        cost_per_action = 0.6 if order_type == "channel" else 0.4
        total_cost = quantity * cost_per_action

        balance = await balance_service.get_balance(current_user["id"])
        if balance < total_cost:
            raise HTTPException(status_code=400, detail="Недостаточно средств для создания заказа")

        # Списание средств и создание заказа
        await balance_service.decrease_balance(current_user["id"], total_cost)
        order = await order_service.create_order(
            user_id=current_user["id"],
            order_type=order_type,
            target_url=target_url,
            quantity=quantity,
            cost_per_action=cost_per_action,
            total_cost=total_cost,
        )

        # Отправляем уведомление пользователю
        await send_notification(
            telegram_client,
            user_id=current_user["id"],
            text=(
                f"✅ Заказ успешно создан!\n\n"
                f"<b>Тип:</b> {order_type}\n"
                f"<b>Количество:</b> {quantity}\n"
                f"<b>Стоимость:</b> {total_cost:.2f} UZT"
            ),
            message_type="success",
        )

        logger.info(f"[Orders] User {current_user['id']} created order #{order.id}")
        return {"ok": True, "order_id": order.id, "total_cost": total_cost}

    except Exception as e:
        logger.exception("[Orders] Failed to create order")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# ----------------------------
# 🔹 Получение своих заказов
# ----------------------------

@router.get("/", response_model=List[Dict[str, Any]])
async def list_user_orders(
    current_user: Dict[str, Any] = Depends(get_current_user),
    order_service: OrderService = Depends(get_order_service),
):
    """
    📦 Возвращает список заказов пользователя.
    """
    try:
        orders = await order_service.list_user_orders(current_user["id"])
        logger.info(f"[Orders] {current_user['id']} fetched their orders ({len(orders)} total)")
        return orders
    except Exception as e:
        logger.exception("[Orders] Failed to fetch user orders")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# ----------------------------
# 🔹 Детали конкретного заказа
# ----------------------------

@router.get("/{order_id}", response_model=Dict[str, Any])
async def get_order_details(
    order_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
    order_service: OrderService = Depends(get_order_service),
):
    """
    🔍 Возвращает детали конкретного заказа.
    """
    try:
        order = await order_service.get_order(order_id, user_id=current_user["id"])
        if not order:
            raise HTTPException(status_code=404, detail="Заказ не найден")
        return order
    except Exception as e:
        logger.exception("[Orders] Failed to fetch order details")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# ----------------------------
# 🔹 Отмена заказа
# ----------------------------

@router.post("/{order_id}/cancel", response_model=Dict[str, Any])
async def cancel_order(
    order_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
    order_service: OrderService = Depends(get_order_service),
    balance_service: BalanceService = Depends(get_balance_service),
    telegram_client: TelegramClient = Depends(),
):
    """
    ❌ Отменяет заказ и возвращает оставшиеся UZT пользователю.
    """
    try:
        refund_amount = await order_service.cancel_order(order_id, user_id=current_user["id"])
        if refund_amount > 0:
            await balance_service.increase_balance(current_user["id"], refund_amount)

            await send_notification(
                telegram_client,
                user_id=current_user["id"],
                text=f"Ваш заказ #{order_id} отменён. Возврат: {refund_amount:.2f} UZT 💰",
                message_type="info",
            )

        logger.info(f"[Orders] User {current_user['id']} canceled order #{order_id}")
        return {"ok": True, "order_id": order_id, "refund": refund_amount}
    except Exception as e:
        logger.exception("[Orders] Failed to cancel order")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# ----------------------------
# 🔹 Статистика заказов
# ----------------------------

@router.get("/stats/summary", response_model=Dict[str, Any])
async def get_orders_summary(
    current_user: Dict[str, Any] = Depends(get_current_user),
    order_service: OrderService = Depends(get_order_service),
):
    """
    📊 Краткая статистика заказов пользователя.
    """
    try:
        summary = await order_service.get_user_summary(user_id=current_user["id"])
        return summary
    except Exception as e:
        logger.exception("[Orders] Failed to get summary")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
