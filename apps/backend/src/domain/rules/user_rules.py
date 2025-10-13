"""
Uzinex Boost — User Rules
=========================

Бизнес-правила, связанные с пользователями платформы Uzinex Boost.

Назначение:
-----------
Определяют возможности и ограничения пользователей в зависимости от их статуса:
- верификация, блокировка, рейтинг, роль;
- разрешения на публикацию заказов, выполнение заданий, переводы средств;
- политика активности и доверия.

Используется в:
- domain.services.user
- domain.services.order
- domain.services.task
- adapters.security
- api.v1.routes.user
"""

from __future__ import annotations
from typing import Dict, Any
from datetime import datetime, timedelta

from domain.rules.base import BaseRule
from db.models.user_model import User


# -------------------------------------------------
# 🔹 Константы политики
# -------------------------------------------------
MIN_RATING_TO_PUBLISH_ORDER = 3.5
MIN_RATING_TO_TAKE_TASK = 2.0
UNVERIFIED_ORDER_LIMIT = 2
MAX_INACTIVE_DAYS = 180  # после этого пользователь считается "спящим"


# -------------------------------------------------
# 🔹 Правила пользователя
# -------------------------------------------------
class UserRules(BaseRule):
    """
    Правила допустимости действий пользователя на платформе.
    """

    rule_name = "UserRules"

    # -------------------------------------------------
    # 🔸 Проверка активности пользователя
    # -------------------------------------------------
    @classmethod
    async def is_active(cls, user: User):
        """
        Проверяет, активен ли пользователь (не заблокирован и не спящий).
        """
        if not user.is_active:
            return await cls._deny("Аккаунт неактивен — действия невозможны")
        if user.is_blocked:
            return await cls._deny("Пользователь заблокирован администрацией")
        if user.last_login and (datetime.utcnow() - user.last_login) > timedelta(days=MAX_INACTIVE_DAYS):
            return await cls._deny("Аккаунт долго не использовался — требуется повторная активация")
        return await cls._allow("Пользователь активен", {"user_id": user.id})

    # -------------------------------------------------
    # 🔸 Проверка верификации пользователя
    # -------------------------------------------------
    @classmethod
    async def is_verified(cls, user: User):
        """
        Проверяет, прошёл ли пользователь верификацию.
        """
        if not user.is_verified:
            return await cls._deny("Требуется верификация аккаунта для выполнения данного действия")
        return await cls._allow("Пользователь верифицирован")

    # -------------------------------------------------
    # 🔸 Проверка возможности публиковать заказы
    # -------------------------------------------------
    @classmethod
    async def can_publish_order(cls, user: User, existing_orders_count: int):
        """
        Проверяет, может ли пользователь создавать новые заказы.
        """
        if not user.is_verified and existing_orders_count >= UNVERIFIED_ORDER_LIMIT:
            return await cls._deny("Неверифицированный пользователь может иметь максимум 2 активных заказа")

        if user.rating is not None and user.rating < MIN_RATING_TO_PUBLISH_ORDER:
            return await cls._deny(f"Минимальный рейтинг для публикации заказов — {MIN_RATING_TO_PUBLISH_ORDER}")

        return await cls._allow("Разрешено публиковать заказ", {"rating": user.rating})

    # -------------------------------------------------
    # 🔸 Проверка возможности брать задания
    # -------------------------------------------------
    @classmethod
    async def can_take_task(cls, user: User):
        """
        Проверяет, может ли пользователь брать задания на выполнение.
        """
        if not user.is_verified:
            return await cls._deny("Для выполнения заданий требуется верификация")
        if user.rating and user.rating < MIN_RATING_TO_TAKE_TASK:
            return await cls._deny(f"Минимальный рейтинг для выполнения заданий — {MIN_RATING_TO_TAKE_TASK}")
        return await cls._allow("Пользователь может выполнять задания", {"rating": user.rating})

    # -------------------------------------------------
    # 🔸 Проверка возможности переводить средства
    # -------------------------------------------------
    @classmethod
    async def can_transfer(cls, user: User):
        """
        Проверяет, может ли пользователь выполнять переводы.
        """
        if not user.is_verified:
            return await cls._deny("Для перевода средств требуется верификация личности")
        if not user.is_active or user.is_blocked:
            return await cls._deny("Переводы недоступны: аккаунт неактивен или заблокирован")
        return await cls._allow("Пользователь может переводить средства")

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
