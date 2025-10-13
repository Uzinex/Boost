"""
Uzinex Boost — User Cache Adapter
=================================

Адаптер для кэширования пользовательских профилей и Telegram WebApp сессий.

Используется для:
- хранения кратких профилей пользователей (id, роль, баланс),
- кэширования проверенных initData (Telegram WebApp auth),
- ускоренной проверки ролей и статусов без SQL-запросов,
- временного хранения токенов и активных сессий.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from datetime import timedelta

from .base import CacheBackend


class UserCache:
    """
    Класс для кэширования данных пользователя и его WebApp-сессий.
    """

    def __init__(
        self,
        cache: CacheBackend,
        namespace: str = "users",
        ttl_profile: int = 600,
        ttl_session: int = 900,
    ):
        """
        :param cache: экземпляр CacheBackend (RedisCache / MemoryCache)
        :param namespace: префикс ключей
        :param ttl_profile: TTL кэша профиля (10 минут)
        :param ttl_session: TTL Telegram WebApp сессии (15 минут)
        """
        self.cache = cache
        self.namespace = namespace
        self.ttl_profile = ttl_profile
        self.ttl_session = ttl_session

    # ----------------------------
    # 🔹 Ключи
    # ----------------------------

    def _key(self, *parts: Any) -> str:
        """Формирует namespaced ключ."""
        return self.cache.build_key(self.namespace, *parts)

    # ----------------------------
    # 🔹 Профиль пользователя
    # ----------------------------

    async def set_profile(self, user_id: str, profile_data: Dict[str, Any]) -> bool:
        """
        Кэширует краткий профиль пользователя.
        Ожидается словарь:
        {
            "id": "uuid",
            "tg_id": 123456,
            "username": "john",
            "balance": 145.7,
            "role": "user",
            "status": "active"
        }
        """
        key = self._key("profile", user_id)
        return await self.cache.set(key, self.cache.to_json(profile_data), expire=self.ttl_profile)

    async def get_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Возвращает профиль пользователя, если он есть в кэше."""
        key = self._key("profile", user_id)
        raw = await self.cache.get(key)
        if not raw:
            return None
        return self.cache.from_json(raw)

    async def invalidate_profile(self, user_id: str) -> None:
        """Удаляет кэш профиля (например, после обновления баланса)."""
        key = self._key("profile", user_id)
        await self.cache.delete(key)

    async def refresh_profile_ttl(self, user_id: str) -> bool:
        """Обновляет TTL профиля."""
        key = self._key("profile", user_id)
        return await self.cache.expire(key, self.ttl_profile)

    # ----------------------------
    # 🔹 Telegram WebApp сессия
    # ----------------------------

    async def cache_session(self, session_hash: str, user_id: str, data: Dict[str, Any]) -> bool:
        """
        Сохраняет проверенные данные Telegram WebApp initData.

        :param session_hash: HMAC-хеш Telegram initData (уникальный для сессии)
        :param user_id: id пользователя
        :param data: валидированные данные Telegram WebApp (username, auth_date и т.д.)
        """
        key = self._key("session", session_hash)
        payload = {"user_id": user_id, "data": data}
        return await self.cache.set(key, self.cache.to_json(payload), expire=self.ttl_session)

    async def get_session(self, session_hash: str) -> Optional[Dict[str, Any]]:
        """Возвращает данные Telegram WebApp-сессии, если она ещё активна."""
        key = self._key("session", session_hash)
        raw = await self.cache.get(key)
        if not raw:
            return None
        return self.cache.from_json(raw)

    async def invalidate_session(self, session_hash: str) -> None:
        """Удаляет WebApp-сессию (например, при logout)."""
        key = self._key("session", session_hash)
        await self.cache.delete(key)

    async def is_session_active(self, session_hash: str) -> bool:
        """Проверяет, активна ли сессия (initData не просрочена)."""
        key = self._key("session", session_hash)
        return await self.cache.exists(key)

    # ----------------------------
    # 🔹 Быстрые проверки
    # ----------------------------

    async def get_role(self, user_id: str) -> Optional[str]:
        """
        Возвращает роль пользователя ('user' / 'admin'), если профиль в кэше.
        """
        profile = await self.get_profile(user_id)
        return profile.get("role") if profile else None

    async def is_admin(self, user_id: str) -> bool:
        """Проверяет, является ли пользователь админом (по кэшу)."""
        role = await self.get_role(user_id)
        return role == "admin"

    async def is_active(self, user_id: str) -> bool:
        """Проверяет, активен ли пользователь (по кэшу)."""
        profile = await self.get_profile(user_id)
        return profile is not None and profile.get("status") == "active"

    async def update_balance_in_cache(self, user_id: str, new_balance: float) -> None:
        """
        Обновляет баланс в кэшированном профиле, не перезаписывая другие поля.
        """
        profile = await self.get_profile(user_id)
        if not profile:
            return
        profile["balance"] = new_balance
        await self.set_profile(user_id, profile)

    # ----------------------------
    # 🔹 Сводка / утилиты
    # ----------------------------

    async def get_summary(self, user_id: str) -> Dict[str, Any]:
        """
        Возвращает сводку для WebApp:
        {
            "user_id": ...,
            "username": ...,
            "role": ...,
            "balance": ...,
            "is_active": True/False
        }
        """
        profile = await self.get_profile(user_id)
        if not profile:
            return {"user_id": user_id, "is_active": False}
        return {
            "user_id": profile.get("id"),
            "username": profile.get("username"),
            "role": profile.get("role"),
            "balance": profile.get("balance"),
            "is_active": profile.get("status") == "active",
        }
