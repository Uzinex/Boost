"""
Uzinex Boost — Base Repository
===============================

Базовый класс репозитория для работы с SQLAlchemy (Async ORM).

Назначение:
- предоставляет стандартные CRUD-операции;
- инкапсулирует доступ к БД;
- служит родительским классом для всех конкретных репозиториев.

Используется в:
- db.repositories.*
- domain.services.*
"""

from __future__ import annotations
from typing import Generic, TypeVar, Type, List, Optional, Any, Dict

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

# Тип для обобщённого класса
T = TypeVar("T")

class BaseRepository(Generic[T]):
    """
    Базовый универсальный репозиторий (CRUD для моделей ORM).
    """

    def __init__(self, session: AsyncSession, model: Type[T]):
        self.session = session
        self.model = model

    # -------------------------------------------------
    # 🔹 CREATE
    # -------------------------------------------------
    async def create(self, data: Dict[str, Any]) -> T:
        """
        Создаёт новую запись в базе.
        """
        obj = self.model(**data)
        self.session.add(obj)
        try:
            await self.session.commit()
            await self.session.refresh(obj)
            return obj
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise RuntimeError(f"Database error on create: {e}")

    # -------------------------------------------------
    # 🔹 READ
    # -------------------------------------------------
    async def get(self, obj_id: int) -> Optional[T]:
        """
        Возвращает запись по ID.
        """
        result = await self.session.execute(select(self.model).where(self.model.id == obj_id))
        return result.scalar_one_or_none()

    async def list(self, skip: int = 0, limit: int = 100) -> List[T]:
        """
        Возвращает список записей.
        """
        result = await self.session.execute(select(self.model).offset(skip).limit(limit))
        return result.scalars().all()

    async def get_by_field(self, field_name: str, value: Any) -> Optional[T]:
        """
        Универсальный поиск по указанному полю.
        """
        field = getattr(self.model, field_name, None)
        if not field:
            raise AttributeError(f"Model {self.model.__name__} has no attribute '{field_name}'")
        result = await self.session.execute(select(self.model).where(field == value))
        return result.scalar_one_or_none()

    # -------------------------------------------------
    # 🔹 UPDATE
    # -------------------------------------------------
    async def update(self, obj_id: int, data: Dict[str, Any]) -> Optional[T]:
        """
        Обновляет запись по ID.
        """
        await self.session.execute(
            update(self.model)
            .where(self.model.id == obj_id)
            .values(**data)
            .execution_options(synchronize_session="fetch")
        )
        try:
            await self.session.commit()
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise RuntimeError(f"Database error on update: {e}")

        return await self.get(obj_id)

    # -------------------------------------------------
    # 🔹 DELETE
    # -------------------------------------------------
    async def delete(self, obj_id: int) -> bool:
        """
        Удаляет запись по ID.
        """
        try:
            await self.session.execute(delete(self.model).where(self.model.id == obj_id))
            await self.session.commit()
            return True
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise RuntimeError(f"Database error on delete: {e}")

    # -------------------------------------------------
    # 🔹 COUNT
    # -------------------------------------------------
    async def count(self) -> int:
        """
        Возвращает общее количество записей.
        """
        from sqlalchemy import func
        result = await self.session.execute(select(func.count()).select_from(self.model))
        return result.scalar() or 0
