"""
Uzinex Boost — Stats Service
=============================

Сервис аналитики и статистики платформы.

Назначение:
- Собирает агрегированные метрики системы (пользователи, задания, баланс, транзакции);
- Используется для дашбордов, административной панели и API `/system/stats`;
- Работает асинхронно с PostgreSQL и Redis;
- Кэширует результаты для оптимизации нагрузки.

Интеграции:
- db.repositories.*
- adapters.cache.RedisCache
"""

from __future__ import annotations
import time
import logging
from typing import Any, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from adapters.cache.redis_cache import RedisCache

logger = logging.getLogger("uzinex.domain.stats")


class StatsService:
    """
    StatsService — агрегатор аналитических данных о платформе.
    """

    def __init__(self, db_session: AsyncSession, cache: Optional[RedisCache] = None):
        self.db = db_session
        self.cache = cache

    # -------------------------------------------------
    # 🔹 Основной метод получения статистики
    # -------------------------------------------------
    async def get_platform_stats(self, use_cache: bool = True) -> Dict[str, Any]:
        """
        Собирает сводную статистику по платформе:
        - количество пользователей
        - количество заданий
        - активные заказы
        - общий оборот (сумма всех платежей)
        - средний баланс пользователя
        """
        cache_key = "stats:platform_summary"
        if use_cache and self.cache:
            cached = await self.cache.get(cache_key)
            if cached:
                logger.debug("📦 Stats fetched from cache")
                return self.cache.from_json(cached)

        start = time.perf_counter()

        try:
            # Общее количество пользователей
            users = await self._count("users")

            # Общее количество заданий
            tasks = await self._count("tasks")

            # Активные заказы
            orders_active = await self._count("orders", where="status = 'active'")

            # Общая сумма платежей
            total_payments = await self._sum("payments", "amount", where="status = 'completed'")

            # Средний баланс пользователя
            avg_balance = await self._avg("balances", "amount")

            stats = {
                "users_total": users,
                "tasks_total": tasks,
                "orders_active": orders_active,
                "payments_total": float(total_payments or 0),
                "avg_balance": float(avg_balance or 0),
                "elapsed_seconds": round(time.perf_counter() - start, 3),
            }

            # Сохраняем в кэш (TTL = 60 сек)
            if self.cache:
                await self.cache.set(cache_key, stats, expire=60)

            logger.info(
                f"📊 Stats summary → users={users}, tasks={tasks}, orders={orders_active}, "
                f"payments={total_payments}, avg_balance={avg_balance}"
            )
            return stats

        except Exception as e:
            logger.error(f"❌ Failed to collect platform stats: {e}")
            return {"error": str(e)}

    # -------------------------------------------------
    # 🔹 Вспомогательные SQL-методы
    # -------------------------------------------------
    async def _count(self, table: str, where: Optional[str] = None) -> int:
        """Подсчитывает количество строк в таблице."""
        query = f"SELECT COUNT(*) FROM {table}"
        if where:
            query += f" WHERE {where}"
        result = await self.db.execute(text(query))
        return int(result.scalar() or 0)

    async def _sum(self, table: str, column: str, where: Optional[str] = None) -> float:
        """Суммирует значения столбца."""
        query = f"SELECT COALESCE(SUM({column}), 0) FROM {table}"
        if where:
            query += f" WHERE {where}"
        result = await self.db.execute(text(query))
        return float(result.scalar() or 0)

    async def _avg(self, table: str, column: str, where: Optional[str] = None) -> float:
        """Вычисляет среднее значение по столбцу."""
        query = f"SELECT COALESCE(AVG({column}), 0) FROM {table}"
        if where:
            query += f" WHERE {where}"
        result = await self.db.execute(text(query))
        return float(result.scalar() or 0)
