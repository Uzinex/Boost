"""
Uzinex Boost — Rate Limit Adapter
=================================

Асинхронный механизм антиспама и ограничения частоты действий (rate limiting).

Используется для:
- предотвращения флуда при выполнении заданий,
- ограничения частоты создания заказов и пополнений,
- защиты API и WebApp от повторных вызовов.
"""

from __future__ import annotations

from datetime import timedelta
from typing import Any, Optional

from .base import CacheBackend
from .exceptions import RateLimitExceeded


class RateLimiter:
    """
    Реализация простого rate-limit механизма на Redis (через CacheBackend).

    Поддерживает стратегию:
    - фиксированное окно (fixed window counter)
    - ограничение по пользователю, IP или действию
    """

    def __init__(
        self,
        cache: CacheBackend,
        namespace: str = "ratelimit",
        ttl: int = 10,
        limit: int = 5,
    ):
        """
        :param cache: экземпляр CacheBackend (обычно RedisCache)
        :param namespace: префикс для ключей
        :param ttl: окно времени в секундах (например, 10 сек)
        :param limit: максимальное количество действий за ttl
        """
        self.cache = cache
        self.namespace = namespace
        self.ttl = ttl
        self.limit = limit

    def _key(self, scope: str, identifier: Any) -> str:
        """
        Формирует namespaced ключ, например:
        ratelimit:task_claim:user_123
        """
        return self.cache.build_key(self.namespace, scope, str(identifier))

    # --------------------------
    # 🔹 Основные методы
    # --------------------------

    async def check(self, scope: str, identifier: Any) -> None:
        """
        Проверяет, не превышен ли лимит.

        :param scope: контекст (например "task_claim", "deposit", "api_call")
        :param identifier: уникальный ID (user_id, ip, tg_id)
        :raises RateLimitExceeded: если лимит превышен
        """
        key = self._key(scope, identifier)
        count = await self.cache.incr(key, amount=1, expire=self.ttl)

        if count > self.limit:
            retry_after = await self.get_ttl_remaining(key)
            raise RateLimitExceeded(retry_after or self.ttl, key=key)

    async def get_ttl_remaining(self, key: str) -> Optional[int]:
        """
        Возвращает оставшееся время до сброса лимита (если доступно).
        """
        try:
            # Для RedisCache — TTL есть, но в MemoryCache может не быть
            ttl_method = getattr(self.cache, "get_ttl", None)
            if callable(ttl_method):
                return await ttl_method(key)
        except Exception:
            return None
        return None

    async def reset(self, scope: str, identifier: Any) -> None:
        """
        Сбрасывает счётчик лимита для конкретного пользователя/действия.
        """
        key = self._key(scope, identifier)
        await self.cache.delete(key)

    async def allow_once(self, scope: str, identifier: Any) -> bool:
        """
        Проверка «однократного разрешения» в окне TTL.
        Возвращает True, если действие можно выполнить впервые.
        False, если пользователь уже делал это в текущем окне.
        """
        key = self._key(scope, identifier)
        exists = await self.cache.exists(key)
        if exists:
            return False
        await self.cache.set(key, "1", expire=self.ttl)
        return True

    # --------------------------
    # 🔹 Утилита: контекстный менеджер
    # --------------------------

    def guard(self, scope: str, identifier: Any):
        """
        Асинхронный контекстный менеджер, выполняющий проверку перед блоком кода.
        Пример:
            async with limiter.guard("task_submit", user_id):
                await service.submit_task(...)
        """
        return _RateLimitGuard(self, scope, identifier)


class _RateLimitGuard:
    """Контекстный менеджер для RateLimiter."""

    def __init__(self, limiter: RateLimiter, scope: str, identifier: Any):
        self.limiter = limiter
        self.scope = scope
        self.identifier = identifier

    async def __aenter__(self):
        await self.limiter.check(self.scope, self.identifier)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return False  # не подавляем исключения
