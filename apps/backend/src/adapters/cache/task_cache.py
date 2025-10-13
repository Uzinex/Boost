"""
Uzinex Boost — Task Cache Adapter
=================================

Адаптер для кэширования заданий (tasks) и временных подтверждений выполнения (proofs).

Используется для:
- хранения активных задач пользователя,
- защиты от повторной выдачи того же задания,
- временного хранения proof до подтверждения админом,
- ускорения выдачи заданий без лишних SQL-запросов.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from datetime import timedelta

from .base import CacheBackend


class TaskCache:
    """
    Класс для кэширования заданий и proof-данных.

    Работает через Redis (CacheBackend).
    TTL по умолчанию — 5 минут для активных задач, 15 минут для proof.
    """

    def __init__(
        self,
        cache: CacheBackend,
        namespace: str = "tasks",
        ttl_active: int = 300,
        ttl_proof: int = 900,
    ):
        """
        :param cache: экземпляр CacheBackend (RedisCache или MemoryCache)
        :param namespace: префикс ключей
        :param ttl_active: TTL активных заданий пользователя
        :param ttl_proof: TTL временного хранения proof-данных
        """
        self.cache = cache
        self.namespace = namespace
        self.ttl_active = ttl_active
        self.ttl_proof = ttl_proof

    # ----------------------------
    # 🔹 Ключи
    # ----------------------------

    def _key(self, *parts: Any) -> str:
        """Формирует namespaced ключ."""
        return self.cache.build_key(self.namespace, *parts)

    # ----------------------------
    # 🔹 Активные задания
    # ----------------------------

    async def cache_active_task(self, user_id: str, task_id: str, order_id: str) -> bool:
        """
        Сохраняет активное задание для пользователя.
        Используется при выдаче нового задания.
        """
        key = self._key("active", user_id)
        data = {"task_id": task_id, "order_id": order_id}
        return await self.cache.set(key, self.cache.to_json(data), expire=self.ttl_active)

    async def get_active_task(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Возвращает текущее активное задание пользователя (если есть)."""
        key = self._key("active", user_id)
        raw = await self.cache.get(key)
        if not raw:
            return None
        return self.cache.from_json(raw)

    async def clear_active_task(self, user_id: str) -> None:
        """Удаляет активное задание пользователя (после submit или timeout)."""
        key = self._key("active", user_id)
        await self.cache.delete(key)

    async def is_task_active(self, user_id: str, task_id: str) -> bool:
        """
        Проверяет, соответствует ли активное задание конкретному ID.
        """
        active = await self.get_active_task(user_id)
        return bool(active and active.get("task_id") == task_id)

    # ----------------------------
    # 🔹 Proof (временные подтверждения)
    # ----------------------------

    async def cache_proof(self, task_id: str, proof_data: Dict[str, Any]) -> bool:
        """
        Кэширует временные данные подтверждения выполнения задания (proof).
        Proof хранится до проверки админом или авто-проверки.
        """
        key = self._key("proof", task_id)
        return await self.cache.set(key, self.cache.to_json(proof_data), expire=self.ttl_proof)

    async def get_proof(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Возвращает proof-данные, если они ещё не удалены или не просрочены.
        """
        key = self._key("proof", task_id)
        raw = await self.cache.get(key)
        if not raw:
            return None
        return self.cache.from_json(raw)

    async def delete_proof(self, task_id: str) -> None:
        """Удаляет proof после обработки (approve/reject)."""
        key = self._key("proof", task_id)
        await self.cache.delete(key)

    # ----------------------------
    # 🔹 Анти-дублирование заданий
    # ----------------------------

    async def mark_task_given(self, user_id: str, order_id: str) -> bool:
        """
        Помечает, что пользователю уже выдавалось задание по данному заказу.
        Это защищает от повторной выдачи.
        """
        key = self._key("given", user_id, order_id)
        return await self.cache.set(key, "1", expire=self.ttl_active)

    async def was_task_given(self, user_id: str, order_id: str) -> bool:
        """Проверяет, выдавалось ли пользователю уже задание по заказу."""
        key = self._key("given", user_id, order_id)
        return await self.cache.exists(key)

    async def clear_given_tasks(self, user_id: str) -> None:
        """Очищает историю выданных заданий для пользователя (при сбросе)."""
        pattern = self._key("given", user_id, "*")
        keys = []
        try:
            if hasattr(self.cache, "keys"):
                keys = await self.cache.keys(pattern)
        except Exception:
            pass

        for k in keys:
            await self.cache.delete(k)

    # ----------------------------
    # 🔹 Сводка по заданиям
    # ----------------------------

    async def get_user_summary(self, user_id: str) -> Dict[str, Any]:
        """
        Возвращает краткую сводку по состоянию задач пользователя.
        """
        active = await self.get_active_task(user_id)
        return {
            "has_active_task": bool(active),
            "active_task_id": active.get("task_id") if active else None,
            "active_order_id": active.get("order_id") if active else None,
        }
