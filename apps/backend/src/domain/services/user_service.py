"""
Uzinex Boost — User Service
===========================

Сервис для управления пользователями системы Uzinex Boost.

Назначение:
-----------
Реализует ключевые бизнес-операции с пользователями:
- регистрация и активация;
- обновление профиля;
- верификация;
- блокировка и удаление;
- аналитика по пользователям.

Используется в:
- api.v1.routes.user
- domain.rules.user_rules
- domain.events.user_events
- db.repositories.user_repository
"""

from __future__ import annotations
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from domain.services.base import BaseService
from domain.rules.user_rules import UserRules
from domain.events.user_events import (
    UserRegisteredEvent,
    UserVerifiedEvent,
    UserProfileUpdatedEvent,
    UserDeactivatedEvent,
    UserDeletedEvent,
)
from db.repositories.user_repository import UserRepository


class UserService(BaseService):
    """
    Управляет жизненным циклом пользователей.
    """

    def __init__(self, session: AsyncSession):
        super().__init__(session)
        self.user_repo = UserRepository(session)

    # -------------------------------------------------
    # 🔹 Регистрация нового пользователя
    # -------------------------------------------------
    async def register_user(
        self,
        email: str,
        username: str,
        password_hash: str,
        referral_id: Optional[int] = None,
    ):
        """
        Создаёт нового пользователя и публикует событие регистрации.
        """
        # Проверяем уникальность email / username
        existing = await self.user_repo.get_by_email(email)
        if existing:
            return {"success": False, "message": "Пользователь с таким email уже существует"}

        user = await self.user_repo.create_user(
            email=email,
            username=username,
            password_hash=password_hash,
            referral_id=referral_id,
        )

        await self.publish_event(
            UserRegisteredEvent(
                user_id=user.id,
                email=user.email,
                username=user.username,
                referral_id=referral_id,
            )
        )
        await self.commit()
        await self.log(f"Пользователь зарегистрирован: {username}")
        return {"success": True, "user_id": user.id}

    # -------------------------------------------------
    # 🔹 Подтверждение верификации
    # -------------------------------------------------
    async def verify_user(self, user_id: int):
        """
        Подтверждает аккаунт пользователя (email / KYC).
        """
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            return {"success": False, "message": "Пользователь не найден"}

        user.is_verified = True
        await self.commit()

        await self.publish_event(UserVerifiedEvent(user_id=user.id, email=user.email))
        await self.log(f"Пользователь верифицирован: {user.email}")
        return {"success": True, "message": "Аккаунт подтверждён"}

    # -------------------------------------------------
    # 🔹 Обновление профиля
    # -------------------------------------------------
    async def update_profile(
        self,
        user_id: int,
        username: Optional[str] = None,
        full_name: Optional[str] = None,
        bio: Optional[str] = None,
    ):
        """
        Обновляет профиль пользователя с проверкой правил.
        """
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            return {"success": False, "message": "Пользователь не найден"}

        can_operate = await UserRules.can_operate(user_id, self.user_repo)
        if not can_operate.is_allowed:
            return {"success": False, "message": can_operate.message}

        updated_user = await self.user_repo.update_profile(
            user_id=user_id, username=username, full_name=full_name, bio=bio
        )

        await self.publish_event(
            UserProfileUpdatedEvent(
                user_id=user_id,
                username=updated_user.username,
                full_name=updated_user.full_name,
                bio=updated_user.bio,
            )
        )
        await self.commit()
        await self.log(f"Профиль обновлён: {user_id}")
        return {"success": True, "message": "Профиль успешно обновлён"}

    # -------------------------------------------------
    # 🔹 Деактивация пользователя
    # -------------------------------------------------
    async def deactivate_user(self, user_id: int, reason: Optional[str] = None):
        """
        Деактивирует (блокирует) пользователя.
        """
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            return {"success": False, "message": "Пользователь не найден"}

        user.is_active = False
        await self.commit()

        await self.publish_event(
            UserDeactivatedEvent(user_id=user_id, reason=reason or "Manual block")
        )
        await self.log(f"Пользователь деактивирован: {user_id}")
        return {"success": True, "message": "Пользователь деактивирован"}

    # -------------------------------------------------
    # 🔹 Удаление пользователя
    # -------------------------------------------------
    async def delete_user(self, user_id: int, deleted_by_admin: bool = False):
        """
        Полностью удаляет пользователя из системы.
        """
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            return {"success": False, "message": "Пользователь не найден"}

        await self.user_repo.delete(user_id)
        await self.publish_event(
            UserDeletedEvent(user_id=user_id, deleted_by_admin=deleted_by_admin)
        )
        await self.commit()
        await self.log(f"Пользователь удалён: {user_id}")
        return {"success": True, "message": "Аккаунт успешно удалён"}

    # -------------------------------------------------
    # 🔹 Получение статистики пользователей
    # -------------------------------------------------
    async def get_user_stats(self):
        """
        Возвращает агрегированную статистику по пользователям.
        """
        total_users = await self.user_repo.count_all()
        verified_users = await self.user_repo.count_verified()
        active_users = await self.user_repo.count_active()

        stats = {
            "total": total_users,
            "verified": verified_users,
            "active": active_users,
        }

        await self.log(f"Получена статистика пользователей: {stats}")
        return stats
