"""
Uzinex Boost — User Repository
==============================

Репозиторий для управления пользователями платформы Uzinex.

Назначение:
- хранение и извлечение данных пользователей;
- обновление профиля, статуса и баланса;
- аналитика по активности и регистрациям;
- интеграция с балансом, задачами, заказами и рефералами.

Используется в:
- domain.services.user
- api.v1.routes.user
- adapters.auth
"""

from __future__ import annotations
from typing import Optional, List, Dict
from datetime import datetime

from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.user_model import User
from db.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """
    Репозиторий для работы с данными пользователей Uzinex.
    """

    def __init__(self, session: AsyncSession):
        super().__init__(session, User)

    # -------------------------------------------------
    # 🔹 Получить пользователя по ID или email
    # -------------------------------------------------
    async def get_by_id(self, user_id: int) -> Optional[User]:
        """
        Возвращает пользователя по ID.
        """
        result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        """
        Возвращает пользователя по email.
        """
        result = await self.session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    # -------------------------------------------------
    # 🔹 Получить пользователей с фильтрацией
    # -------------------------------------------------
    async def get_all(
        self,
        is_active: Optional[bool] = None,
        is_verified: Optional[bool] = None,
        limit: int = 100,
    ) -> List[User]:
        """
        Возвращает список пользователей (с фильтрацией по активности/верификации).
        """
        query = select(User)
        if is_active is not None:
            query = query.where(User.is_active == is_active)
        if is_verified is not None:
            query = query.where(User.is_verified == is_verified)

        result = await self.session.execute(
            query.order_by(User.created_at.desc()).limit(limit)
        )
        return result.scalars().all()

    # -------------------------------------------------
    # 🔹 Создать нового пользователя
    # -------------------------------------------------
    async def create_user(
        self,
        email: str,
        username: str,
        password_hash: str,
        full_name: Optional[str] = None,
        referral_id: Optional[int] = None,
    ) -> User:
        """
        Создаёт нового пользователя (регистрация через email/password).
        """
        user = User(
            email=email.lower(),
            username=username,
            password_hash=password_hash,
            full_name=full_name,
            referral_id=referral_id,
            created_at=datetime.utcnow(),
        )
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    # -------------------------------------------------
    # 🔹 Обновление данных профиля
    # -------------------------------------------------
    async def update_profile(
        self,
        user_id: int,
        full_name: Optional[str] = None,
        username: Optional[str] = None,
        bio: Optional[str] = None,
    ) -> Optional[User]:
        """
        Обновляет профиль пользователя.
        """
        update_data = {}
        if full_name:
            update_data["full_name"] = full_name
        if username:
            update_data["username"] = username
        if bio:
            update_data["bio"] = bio

        if not update_data:
            return await self.get_by_id(user_id)

        await self.session.execute(
            update(User)
            .where(User.id == user_id)
            .values(**update_data)
            .execution_options(synchronize_session="fetch")
        )
        await self.session.commit()
        return await self.get_by_id(user_id)

    # -------------------------------------------------
    # 🔹 Изменение статуса (активация, блокировка и т.д.)
    # -------------------------------------------------
    async def update_status(
        self, user_id: int, is_active: bool
    ) -> Optional[User]:
        """
        Активирует или деактивирует пользователя.
        """
        await self.session.execute(
            update(User)
            .where(User.id == user_id)
            .values(is_active=is_active)
            .execution_options(synchronize_session="fetch")
        )
        await self.session.commit()
        return await self.get_by_id(user_id)

    # -------------------------------------------------
    # 🔹 Подтверждение email
    # -------------------------------------------------
    async def verify_email(self, user_id: int) -> Optional[User]:
        """
        Устанавливает флаг подтверждения email.
        """
        await self.session.execute(
            update(User)
            .where(User.id == user_id)
            .values(is_verified=True)
        )
        await self.session.commit()
        return await self.get_by_id(user_id)

    # -------------------------------------------------
    # 🔹 Аналитика и статистика
    # -------------------------------------------------
    async def get_stats(self) -> Dict[str, int]:
        """
        Возвращает статистику по пользователям:
        - общее количество,
        - активные,
        - верифицированные.
        """
        result = await self.session.execute(
            select(
                func.count(User.id),
                func.sum(func.case((User.is_active == True, 1), else_=0)),
                func.sum(func.case((User.is_verified == True, 1), else_=0)),
            )
        )
        total, active, verified = result.one_or_none() or (0, 0, 0)
        return {
            "total": total,
            "active": int(active or 0),
            "verified": int(verified or 0),
        }

    # -------------------------------------------------
    # 🔹 Последние зарегистрированные пользователи
    # -------------------------------------------------
    async def get_recent(self, limit: int = 20) -> List[User]:
        """
        Возвращает последние регистрации (для админ-панели).
        """
        result = await self.session.execute(
            select(User)
            .order_by(User.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()

    # -------------------------------------------------
    # 🔹 Поиск по имени, email или username
    # -------------------------------------------------
    async def search(self, query: str, limit: int = 20) -> List[User]:
        """
        Поиск пользователей по email, имени или username.
        """
        like_query = f"%{query.lower()}%"
        result = await self.session.execute(
            select(User).where(
                func.lower(User.email).like(like_query)
                | func.lower(User.username).like(like_query)
                | func.lower(User.full_name).like(like_query)
            ).limit(limit)
        )
        return result.scalars().all()
