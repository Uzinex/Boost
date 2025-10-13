"""
Uzinex Boost — Order Rules
==========================

Бизнес-правила, регулирующие создание, выполнение и завершение заказов.

Назначение:
-----------
Определяет допустимость создания и исполнения заказов:
- проверка минимальной и максимальной цены;
- комиссия платформы;
- сроки выполнения и дедлайны;
- доступность заказа для исполнителя;
- защита от конфликтов и мошенничества.

Используется в:
- domain.services.order
- domain.services.payment
- domain.services.balance
- adapters.analytics
- api.v1.routes.order
"""

from __future__ import annotations
from datetime import datetime, timedelta
from typing import Dict, Any

from domain.rules.base import BaseRule


# -------------------------------------------------
# 🔹 Константы политики
# -------------------------------------------------
MIN_ORDER_PRICE = 10_000.0
MAX_ORDER_PRICE = 50_000_000.0
PLATFORM_FEE_PERCENT = 10.0  # комиссия платформы в %
MAX_ACTIVE_ORDERS_PER_CLIENT = 10
MAX_ACTIVE_ORDERS_PER_PERFORMER = 5
DEFAULT_ORDER_DURATION = timedelta(days=7)  # стандартный срок выполнения


# -------------------------------------------------
# 🔹 Правила заказов
# -------------------------------------------------
class OrderRules(BaseRule):
    """
    Набор бизнес-правил, определяющих корректность и ограничения заказов.
    """

    rule_name = "OrderRules"

    # -------------------------------------------------
    # 🔸 Проверка возможности создания заказа
    # -------------------------------------------------
    @classmethod
    async def can_create_order(cls, client, price: float, active_orders_count: int):
        """
        Проверяет, может ли пользователь создать заказ с указанной ценой.
        """
        if not client.is_verified:
            return await cls._deny("Создание заказов доступно только верифицированным пользователям")

        if price < MIN_ORDER_PRICE:
            return await cls._deny(f"Минимальная стоимость заказа — {MIN_ORDER_PRICE:.0f} UZT")

        if price > MAX_ORDER_PRICE:
            return await cls._deny(f"Сумма заказа превышает лимит {MAX_ORDER_PRICE:.0f} UZT")

        if active_orders_count >= MAX_ACTIVE_ORDERS_PER_CLIENT:
            return await cls._deny("Превышен лимит активных заказов")

        return await cls._allow("Создание заказа разрешено", {"price": price})

    # -------------------------------------------------
    # 🔸 Проверка возможности принять заказ
    # -------------------------------------------------
    @classmethod
    async def can_accept_order(cls, performer, active_orders_count: int):
        """
        Проверяет, может ли исполнитель взять заказ в работу.
        """
        if not performer.is_verified:
            return await cls._deny("Для выполнения заказов требуется пройти верификацию")
        if active_orders_count >= MAX_ACTIVE_ORDERS_PER_PERFORMER:
            return await cls._deny("Превышен лимит активных заказов для исполнителя")
        if performer.rating < 2.5:
            return await cls._deny("Рейтинг ниже минимального уровня для участия в заказах")
        return await cls._allow("Исполнитель может принять заказ", {"rating": performer.rating})

    # -------------------------------------------------
    # 🔸 Проверка допустимости срока выполнения
    # -------------------------------------------------
    @classmethod
    async def validate_deadline(cls, deadline: datetime):
        """
        Проверяет, не превышает ли срок выполнения допустимое значение.
        """
        now = datetime.utcnow()
        max_deadline = now + timedelta(days=30)
        if deadline > max_deadline:
            return await cls._deny("Максимальный срок выполнения заказа — 30 дней")
        if deadline < now:
            return await cls._deny("Дата завершения не может быть в прошлом")
        return await cls._allow("Срок выполнения корректен", {"deadline": deadline.isoformat()})

    # -------------------------------------------------
    # 🔸 Расчёт комиссии платформы
    # -------------------------------------------------
    @classmethod
    async def calculate_fee(cls, price: float) -> Dict[str, Any]:
        """
        Рассчитывает комиссию платформы и чистую сумму исполнителя.
        """
        fee = round(price * PLATFORM_FEE_PERCENT / 100, 2)
        net = round(price - fee, 2)
        return {"fee": fee, "net_amount": net, "percent": PLATFORM_FEE_PERCENT}

    # -------------------------------------------------
    # 🔸 Проверка завершения заказа
    # -------------------------------------------------
    @classmethod
    async def can_complete_order(cls, order_status: str, deadline: datetime):
        """
        Проверяет, можно ли завершить заказ (статус и срок).
        """
        if order_status not in ["in_progress", "review"]:
            return await cls._deny(f"Невозможно завершить заказ в статусе '{order_status}'")
        if datetime.utcnow() > deadline + timedelta(days=3):
            return await cls._deny("Срок завершения заказа истёк — требуется модерация")
        return await cls._allow("Завершение заказа разрешено")

    # -------------------------------------------------
    # 🔸 Проверка отмены заказа
    # -------------------------------------------------
    @classmethod
    async def can_cancel_order(cls, order_status: str, user_role: str):
        """
        Проверяет, имеет ли пользователь право отменить заказ.
        """
        if order_status in ["completed", "cancelled"]:
            return await cls._deny("Заказ уже завершён или отменён")
        if user_role not in ["client", "admin"]:
            return await cls._deny("Отмену может выполнить только заказчик или администратор")
        return await cls._allow("Отмена заказа разрешена", {"role": user_role})

    # -------------------------------------------------
    # 🔹 Вспомогательные методы
    # -------------------------------------------------
    @classmethod
    async def _allow(cls, message: str, meta: Dict[str, Any] | None = None):
        return await cls._result(True, message, meta)

    @classmethod
    async def _deny(cls, message: str, meta: Dict[str, Any] | None = None):
        return await cls._result(False, message, meta)

    @classmethod
    async def _result(cls, allowed: bool, message: str, meta: Dict[str, Any] | None = None):
        from domain.rules.base import RuleResult
        return RuleResult(
            is_allowed=allowed,
            message=message,
            rule_name=cls.rule_name,
            metadata=meta or {},
        )
