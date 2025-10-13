"""
Uzinex Boost — Task Service
===========================

Сервис управления заданиями (Tasks) пользователей.

Назначение:
-----------
Реализует основные сценарии:
- создание задания;
- принятие и выполнение пользователем;
- проверка и утверждение модератором;
- начисление вознаграждения;
- аналитика по активности.

Используется в:
- api.v1.routes.task
- domain.rules.task_rules
- domain.events.task_events
- db.repositories.task_repository
- domain.services.balance_service
"""

from __future__ import annotations
from typing import Optional
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from domain.services.base import BaseService
from domain.rules.task_rules import TaskRules
from domain.events.task_events import (
    TaskCreatedEvent,
    TaskAcceptedEvent,
    TaskCompletedEvent,
    TaskApprovedEvent,
    TaskRejectedEvent,
)
from domain.services.balance_service import BalanceService
from db.repositories.task_repository import TaskRepository
from db.repositories.user_repository import UserRepository


class TaskService(BaseService):
    """
    Управляет заданиями пользователей: создание, выполнение, проверка, оплата.
    """

    def __init__(self, session: AsyncSession):
        super().__init__(session)
        self.task_repo = TaskRepository(session)
        self.user_repo = UserRepository(session)
        self.balance_service = BalanceService(session)

    # -------------------------------------------------
    # 🔹 Создание нового задания
    # -------------------------------------------------
    async def create_task(
        self,
        creator_id: int,
        title: str,
        description: str,
        reward: float,
        deadline: Optional[datetime] = None,
    ):
        """
        Публикует новое задание.
        """
        creator = await self.user_repo.get_by_id(creator_id)
        if not creator:
            return {"success": False, "message": "Пользователь не найден"}

        active_tasks = await self.task_repo.count_active_by_user(creator_id)
        rule = await TaskRules.can_create_task(creator, reward, active_tasks)
        if not rule.is_allowed:
            return {"success": False, "message": rule.message}

        # Проверка баланса (создатель должен заморозить вознаграждение)
        balance = await self.balance_service.get_balance(creator_id)
        if balance is None or balance < reward:
            return {"success": False, "message": "Недостаточно средств на балансе"}

        await self.balance_service.withdraw(creator_id, reward)

        task = await self.task_repo.create_task(
            creator_id=creator_id,
            title=title,
            description=description,
            reward=reward,
            deadline=deadline or datetime.utcnow() + timedelta(days=3),
        )

        await self.publish_event(TaskCreatedEvent(task_id=task.id, creator_id=creator_id, reward=reward))
        await self.commit()
        await self.log(f"Создано задание {task.id} пользователем {creator_id}")
        return {"success": True, "task_id": task.id}

    # -------------------------------------------------
    # 🔹 Взять задание в работу
    # -------------------------------------------------
    async def accept_task(self, performer_id: int, task_id: int):
        """
        Исполнитель принимает задание в выполнение.
        """
        performer = await self.user_repo.get_by_id(performer_id)
        task = await self.task_repo.get_by_id(task_id)

        if not performer or not task:
            return {"success": False, "message": "Пользователь или задание не найдено"}
        if task.status != "open":
            return {"success": False, "message": "Задание недоступно для принятия"}

        active_tasks = await self.task_repo.count_active_by_user(performer_id)
        rule = await TaskRules.can_accept_task(performer, active_tasks)
        if not rule.is_allowed:
            return {"success": False, "message": rule.message}

        task.performer_id = performer_id
        task.status = "in_progress"
        task.accepted_at = datetime.utcnow()

        await self.publish_event(TaskAcceptedEvent(task_id=task.id, performer_id=performer_id))
        await self.commit()
        await self.log(f"Исполнитель {performer_id} принял задание {task_id}")
        return {"success": True, "status": "in_progress"}

    # -------------------------------------------------
    # 🔹 Завершение задания исполнителем
    # -------------------------------------------------
    async def complete_task(self, performer_id: int, task_id: int):
        """
        Исполнитель завершает выполнение задания (отправка на проверку).
        """
        task = await self.task_repo.get_by_id(task_id)
        if not task or task.performer_id != performer_id:
            return {"success": False, "message": "Неверный исполнитель или задание"}

        rule = await TaskRules.can_complete_task(task.status, task.deadline)
        if not rule.is_allowed:
            return {"success": False, "message": rule.message}

        task.status = "review"
        task.completed_at = datetime.utcnow()

        await self.publish_event(TaskCompletedEvent(task_id=task.id, performer_id=performer_id))
        await self.commit()
        await self.log(f"Задание {task_id} завершено исполнителем {performer_id}")
        return {"success": True, "status": "review"}

    # -------------------------------------------------
    # 🔹 Проверка и утверждение модератором
    # -------------------------------------------------
    async def approve_task(self, task_id: int, reviewer_role: str):
        """
        Модератор утверждает выполнение задания.
        """
        task = await self.task_repo.get_by_id(task_id)
        if not task:
            return {"success": False, "message": "Задание не найдено"}

        rule = await TaskRules.can_approve_task(reviewer_role, task.status)
        if not rule.is_allowed:
            return {"success": False, "message": rule.message}

        task.status = "approved"
        task.reviewed_at = datetime.utcnow()

        # Выплата исполнителю
        await self.balance_service.deposit(task.performer_id, task.reward)

        await self.publish_event(TaskApprovedEvent(task_id=task.id, performer_id=task.performer_id, reward=task.reward))
        await self.commit()
        await self.log(f"Задание {task.id} одобрено модератором")
        return {"success": True, "status": "approved"}

    # -------------------------------------------------
    # 🔹 Отклонение задания
    # -------------------------------------------------
    async def reject_task(self, task_id: int, reviewer_role: str, reason: str):
        """
        Модератор отклоняет выполнение задания.
        """
        task = await self.task_repo.get_by_id(task_id)
        if not task:
            return {"success": False, "message": "Задание не найдено"}

        rule = await TaskRules.can_approve_task(reviewer_role, task.status)
        if not rule.is_allowed:
            return {"success": False, "message": rule.message}

        task.status = "rejected"
        task.reviewed_at = datetime.utcnow()
        task.reject_reason = reason

        # Возврат средств заказчику
        await self.balance_service.deposit(task.creator_id, task.reward)

        await self.publish_event(TaskRejectedEvent(task_id=task.id, reason=reason))
        await self.commit()
        await self.log(f"Задание {task.id} отклонено: {reason}")
        return {"success": True, "status": "rejected"}

    # -------------------------------------------------
    # 🔹 Получение заданий пользователя
    # -------------------------------------------------
    async def get_user_tasks(self, user_id: int, role: str, limit: int = 50):
        """
        Возвращает список заданий пользователя (созданных или выполняемых).
        """
        if role == "creator":
            tasks = await self.task_repo.get_by_creator(user_id, limit)
        else:
            tasks = await self.task_repo.get_by_performer(user_id, limit)
        return [t.as_dict() for t in tasks]

    # -------------------------------------------------
    # 🔹 Аналитика по заданиям
    # -------------------------------------------------
    async def get_global_stats(self):
        """
        Возвращает статистику по заданиям.
        """
        stats = await self.task_repo.get_stats()
        await self.log("Получена глобальная статистика заданий")
        return stats
