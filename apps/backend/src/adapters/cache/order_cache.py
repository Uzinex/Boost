"""
Uzinex Boost — Order Cache Adapter
==================================

Адаптер для кэширования данных заказов (orders) в Redis.

Используется для:
- ускоренного доступа к статистике заказов,
- расчёта прогресса выполнения,
- кэширования активных заказов пользователя,
- уменьшения обращений к PostgreSQL.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .base import CacheBackend
from .exceptions import CacheError


class OrderCache:
    """
    Класс для работы с кэшированием заказов.
    Использует Redis (или другой CacheBackend) для хранения метаданных и статистики.
    """

    def __init__(self, cache: CacheBackend, namespace: str = "orders", ttl: int = 300):
        """
        :param cache: экземпляр CacheBackend
        :param namespace: префикс ключей Redis
        :param ttl: время жизни кэша в секундах (по умолчанию 5 минут)
        """
        self.cache = cache
        self.namespace = namespace
        self.ttl = ttl

    # --------------------------
    # 🔹 Основные операции
    # --------------------------

    def _key(self, *parts: Any) -> str:
        """Формирует ключ с namespace."""
        return self.cache.build_key(self.namespace, *parts)

    async def set_order_stats(
        self,
        order_id: str,
        total: int,
        done: int,
        status: str,
        owner_id: Optional[str] = None,
    ) -> bool:
        """
        Сохраняет агрегированную статистику заказа.

        :param order_id: UUID заказа
        :param total: общее количество заданий
        :param done: количество выполненных
        :param status: текущий статус заказа
        :param owner_id: id владельца (для индексации активных заказов)
        """
        key = self._key(order_id, "stats")
        data = {
            "total": total,
            "done": done,
            "status": status,
        }
        if owner_id:
            data["owner_id"] = owner_id

        return await self.cache.set(key, self.cache.to_json(data), expire=self.ttl)

    async def get_order_stats(self, order_id: str) -> Optional[Dict[str, Any]]:
        """Возвращает статистику заказа, если она есть в кэше."""
        key = self._key(order_id, "stats")
        raw = await self.cache.get(key)
        if not raw:
            return None
        return self.cache.from_json(raw)

    async def update_done_count(self, order_id: str, increment: int = 1) -> Optional[int]:
        """
        Увеличивает значение выполненных задач в кэше (done_count).
        Используется при approve задач.
        """
        stats = await self.get_order_stats(order_id)
        if not stats:
            return None
        stats["done"] = int(stats.get("done", 0)) + increment
        await self.cache.set(self._key(order_id, "stats"), self.cache.to_json(stats), expire=self.ttl)
        return stats["done"]

    async def cache_active_orders(self, owner_id: str, order_ids: List[str]) -> bool:
        """
        Кэширует список активных заказов пользователя.
        """
        key = self._key("user", owner_id, "active")
        return await self.cache.set(key, self.cache.to_json(order_ids), expire=self.ttl)

    async def get_active_orders(self, owner_id: str) -> List[str]:
        """
        Возвращает список активных заказов пользователя (если есть).
        """
        key = self._key("user", owner_id, "active")
        data = await self.cache.get(key)
        if not data:
            return []
        return self.cache.from_json(data)

    async def invalidate_order(self, order_id: str) -> None:
        """
        Удаляет кэшированные данные конкретного заказа.
        """
        key = self._key(order_id, "stats")
        await self.cache.delete(key)

    async def invalidate_user_orders(self, owner_id: str) -> None:
        """
        Удаляет кэш активных заказов пользователя.
        """
        key = self._key("user", owner_id, "active")
        await self.cache.delete(key)

    # --------------------------
    # 🔹 Утилиты
    # --------------------------

    async def refresh_ttl(self, order_id: str) -> bool:
        """Обновляет TTL у записи статистики заказа."""
        key = self._key(order_id, "stats")
        return await self.cache.expire(key, self.ttl)

    async def get_progress_percent(self, order_id: str) -> Optional[float]:
        """
        Возвращает процент выполнения заказа, если есть данные в кэше.
        """
        stats = await self.get_order_stats(order_id)
        if not stats:
            return None
        total = max(1, int(stats.get("total", 1)))
        done = int(stats.get("done", 0))
        return round(done / total * 100, 2)

    async def get_summary_for_user(self, owner_id: str) -> Dict[str, Any]:
        """
        Собирает сводную информацию по заказам пользователя.
        (активные заказы, средний прогресс, общее количество выполнений)
        """
        active_orders = await self.get_active_orders(owner_id)
        if not active_orders:
            return {"active_count": 0, "avg_progress": 0.0, "total_done": 0}

        progresses = []
        total_done = 0

        for order_id in active_orders:
            stats = await self.get_order_stats(order_id)
            if stats:
                done = int(stats.get("done", 0))
                total = int(stats.get("total", 1))
                progresses.append(done / max(1, total))
                total_done += done

        avg_progress = round(sum(progresses) / len(progresses) * 100, 2) if progresses else 0.0
        return {
            "active_count": len(active_orders),
            "avg_progress": avg_progress,
            "total_done": total_done,
        }
