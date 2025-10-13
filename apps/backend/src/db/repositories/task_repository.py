"""
Uzinex Boost — Task Repository
===============================

Репозиторий для работы с заданиями (ORM-модель Task).

Назначение:
- управление заданиями, выполняемыми пользователями;
- фиксация выполнения и начисление вознаграждений;
- статистика по активности и выполненным заданиям.

Используется в:
- domain.services.tasks
- api.v1.routes.tasks
- balance/transaction logic
"""

from __future__ import annotations
from datetime import datetime
from typing import List, Optional

from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.task_model import Task, TaskStatus
from db.repositories.base import BaseRepository


class TaskRepository(BaseRepository[Task]):
    """
    Репозиторий для управления заданиями пользователей.
    """

    def __init__(self, session: AsyncSession):
        super().__init__(session, Task)

    # -------------------------------------------------
    # 🔹 Получить задания по пользователю
    # -------------------------------------------------
    async def get_by_user(self, user_id: int, status: Optional[TaskStatus] = None) -> List[Task]:
        """
        Возвращает все задания пользователя, опционально фильтруя по статусу.
        """
        query = select(Task).where(Task.user_id == user_id)
        if status:
            query = query.where(Task.status == status)
        result = await self.session.execute(query.order_by(Task.created_at.desc()))
        return result.scalars().all()

    # -------------------------------------------------
    # 🔹 Получить задания по заказу
    # -------------------------------------------------
    async def get_by_order(self, order_id: int) -> List[Task]:
        """
        Возвращает все задания, связанные с конкретным заказом.
        """
        result = await self.session.execute(
            select(Task)
            .where(Task.order_id == order_id)
            .order_by(Task.created_at.desc())
        )
        return result.scalars().all()

    # -------------------------------------------------
    # 🔹 Отметить задание как выполненное
    # -------------------------------------------------
    async def complete_task(self, task_id: int) -> Optional[Task]:
        """
        Обновляет статус задания на COMPLETED и фиксирует время завершения.
        """
        await self.session.execute(
            update(Task)
            .where(Task.id == task_id)
            .values(
                status=TaskStatus.COMPLETED,
                completed_at=datetime.utcnow(),
            )
            .execution_options(synchronize_session="fetch")
        )
        await self.session.commit()
        return await self.get(task_id)

    # -------------------------------------------------
    # 🔹 Отклонить задание
    # -------------------------------------------------
    async def reject_task(self, task_id: int) -> Optional[Task]:
        """
        Помечает задание как REJECTED.
        """
        await self.session.execute(
            update(Task)
            .where(Task.id == task_id)
            .values(status=TaskStatus.REJECTED)
            .execution_options(synchronize_session="fetch")
        )
        await self.session.commit()
        return await self.get(task_id)

    # -------------------------------------------------
    # 🔹 Подсчёт статистики по задачам пользователя
    # -------------------------------------------------
    async def get_user_stats(self, user_id: int) -> dict:
        """
        Возвращает статистику выполненных заданий пользователем:
        - количество завершённых,
        - количество отклонённых,
        - общая сумма вознаграждения.
        """
        result = await self.session.execute(
            select(
                Task.status,
                func.count(Task.id),
                func.sum(Task.reward_amount),
            ).where(Task.user_id == user_id).group_by(Task.status)
        )

        stats = {status.value: {"count": cnt, "sum": float(total or 0)} for status, cnt, total in result.all()}
        total_tasks = sum(v["count"] for v in stats.values()) if stats else 0
        total_earned = sum(v["sum"] for v in stats.values()) if stats else 0.0

        stats["total"] = {"count": total_tasks, "sum": round(total_earned, 2)}
        return stats

    # -------------------------------------------------
    # 🔹 Получить активные задания
    # -------------------------------------------------
    async def get_active_tasks(self, limit: int = 50) -> List[Task]:
        """
        Возвращает активные задания (в ожидании выполнения).
        """
        result = await self.session.execute(
            select(Task)
            .where(Task.status == TaskStatus.PENDING)
            .order_by(Task.created_at.asc())
            .limit(limit)
        )
        return result.scalars().all()

    # -------------------------------------------------
    # 🔹 Подсчёт общего заработка всех пользователей
    # -------------------------------------------------
    async def get_global_earn_stats(self) -> dict:
        """
        Возвращает общие метрики по всем выполненным заданиям:
        - количество задач;
        - общая сумма вознаграждений.
        """
        result = await self.session.execute(
            select(
                func.count(Task.id),
                func.sum(Task.reward_amount),
            ).where(Task.status == TaskStatus.COMPLETED)
        )
        count, total = result.first() or (0, 0.0)
        return {"completed": count or 0, "total_reward": round(float(total or 0), 2)}
