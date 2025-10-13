"""
Uzinex Boost — Task Rules
=========================

Бизнес-правила, регулирующие задания (tasks) и их выполнение.

Назначение:
-----------
Определяет, кто и при каких условиях может:
- создавать задания;
- брать задания в работу;
- выполнять и получать вознаграждение;
- проверять и одобрять результаты.

Используется в:
- domain.services.task
- domain.services.balance
- domain.services.referral
- adapters.analytics
- api.v1.routes.task
"""

from __future__ import annotations
from datetime import datetime, timedelta
from typing import Dict, Any

from domain.rules.base import BaseRule


# -------------------------------------------------
# 🔹 Константы политики заданий
# -------------------------------------------------
MIN_TASK_REWARD = 2_000.0
MAX_TASK_REWARD = 1_000_000.0
MAX_ACTIVE_TASKS_PER_USER = 5
DEFAULT_TASK_DURATION = timedelta(days=3)
MAX_TASK_DURATION = timedelta(days=14)
REVIEW_PERIOD = timedelta(days=2)  # срок проверки задания модератором


# -------------------------------------------------
# 🔹 Правила заданий
# -------------------------------------------------
class TaskRules(BaseRule):
    """
    Набор правил для проверки допустимости действий с заданиями.
    """

    rule_name = "TaskRules"

    # -------------------------------------------------
    # 🔸 Проверка возможности создания задания
    # -------------------------------------------------
    @classmethod
    async def can_create_task(cls, creator, reward: float, active_tasks_count: int):
        """
        Проверяет, может ли пользователь опубликовать задание.
        """
        if not creator.is_verified:
            return await cls._deny("Публиковать задания могут только верифицированные пользователи")

        if reward < MIN_TASK_REWARD:
            return await cls._deny(f"Минимальное вознаграждение за задание — {MIN_TASK_REWARD:.0f} UZT")

        if reward > MAX_TASK_REWARD:
            return await cls._deny(f"Вознаграждение превышает лимит {MAX_TASK_REWARD:.0f} UZT")

        if active_tasks_count >= MAX_ACTIVE_TASKS_PER_USER:
            return await cls._deny("Превышен лимит активных заданий")

        return await cls._allow("Создание задания разрешено", {"reward": reward})

    # -------------------------------------------------
    # 🔸 Проверка возможности взять задание
    # -------------------------------------------------
    @classmethod
    async def can_accept_task(cls, user, active_tasks_count: int):
        """
        Проверяет, может ли пользователь взять задание в работу.
        """
        if not user.is_verified:
            return await cls._deny("Для выполнения заданий требуется верификация")
        if active_tasks_count >= MAX_ACTIVE_TASKS_PER_USER:
            return await cls._deny("Превышен лимит активных заданий в работе")
        if getattr(user, "rating", 0) < 2.0:
            return await cls._deny("Рейтинг слишком низкий для выполнения заданий")
        return await cls._allow("Пользователь может взять задание", {"rating": user.rating})

    # -------------------------------------------------
    # 🔸 Проверка срока выполнения задания
    # -------------------------------------------------
    @classmethod
    async def validate_deadline(cls, deadline: datetime):
        """
        Проверяет, корректен ли срок выполнения задания.
        """
        now = datetime.utcnow()
        if deadline < now:
            return await cls._deny("Срок выполнения не может быть в прошлом")
        if deadline - now > MAX_TASK_DURATION:
            return await cls._deny("Максимальный срок выполнения задания — 14 дней")
        return await cls._allow("Срок выполнения корректен", {"deadline": deadline.isoformat()})

    # -------------------------------------------------
    # 🔸 Проверка возможности завершить задание
    # -------------------------------------------------
    @classmethod
    async def can_complete_task(cls, task_status: str, deadline: datetime):
        """
        Проверяет, можно ли завершить задание.
        """
        if task_status not in ["in_progress", "review"]:
            return await cls._deny(f"Задание нельзя завершить в статусе '{task_status}'")

        if datetime.utcnow() > deadline + REVIEW_PERIOD:
            return await cls._deny("Срок проверки задания истёк — требуется модерация")

        return await cls._allow("Завершение задания разрешено")

    # -------------------------------------------------
    # 🔸 Проверка вознаграждения за задание
    # -------------------------------------------------
    @classmethod
    async def validate_reward(cls, reward: float):
        """
        Проверяет корректность суммы вознаграждения.
        """
        if reward < MIN_TASK_REWARD:
            return await cls._deny(f"Минимальное вознаграждение — {MIN_TASK_REWARD:.0f} UZT")
        if reward > MAX_TASK_REWARD:
            return await cls._deny(f"Превышено максимальное вознаграждение — {MAX_TASK_REWARD:.0f} UZT")
        return await cls._allow("Вознаграждение корректно", {"reward": reward})

    # -------------------------------------------------
    # 🔸 Проверка возможности одобрить задание
    # -------------------------------------------------
    @classmethod
    async def can_approve_task(cls, reviewer_role: str, task_status: str):
        """
        Проверяет, может ли модератор одобрить задание.
        """
        if reviewer_role not in ["admin", "moderator"]:
            return await cls._deny("Только модератор или администратор может одобрить задание")
        if task_status != "review":
            return await cls._deny("Задание должно находиться на проверке")
        return await cls._allow("Одобрение задания разрешено", {"role": reviewer_role})

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
