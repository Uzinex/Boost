"""
Uzinex Boost — Cache Idempotency Layer
======================================

Модуль реализует защиту от повторных POST-операций
(approve, deposit, transfer и т.п.) через механизм Idempotency-Key.

Используется всеми REST и бот-командами, где возможны повторные запросы.
"""

from __future__ import annotations

import asyncio
from typing import Optional
from datetime import timedelta

from .base import CacheBackend
from .exceptions import IdempotencyConflict


class IdempotencyManager:
    """
    Менеджер идемпотентных операций.
    Проверяет, что операция с данным ключом выполняется только один раз.

    Пример использования:
    ----------------------
        cache = get_cache()
        idm = IdempotencyManager(cache)

        async with idm.guard("deposit:12345"):
            # выполнить только один раз
            await service.approve_deposit(12345)
    """

    def __init__(self, cache: CacheBackend, namespace: str = "idempotency", ttl: int = 60):
        """
        :param cache: экземпляр CacheBackend (RedisCache / MemoryCache)
        :param namespace: префикс для ключей
        :param ttl: время жизни идемпотентного ключа (в секундах)
        """
        self.cache = cache
        self.namespace = namespace
        self.ttl = ttl

    def _key(self, token: str) -> str:
        """Формирует уникальный ключ для хранилища."""
        return self.cache.build_key(self.namespace, token)

    async def check(self, token: str) -> bool:
        """
        Проверяет, зарегистрирован ли данный ключ.

        :return: True — операция уже выполнялась, False — новая.
        """
        key = self._key(token)
        return await self.cache.exists(key)

    async def register(self, token: str) -> None:
        """
        Регистрирует новый идемпотентный ключ.
        Если он уже есть — выбрасывает IdempotencyConflict.
        """
        key = self._key(token)
        already = await self.cache.exists(key)
        if already:
            raise IdempotencyConflict(key)
        await self.cache.set(key, "locked", expire=self.ttl)

    async def release(self, token: str) -> None:
        """
        Снимает блокировку по ключу (если операция завершена или откатилась).
        """
        key = self._key(token)
        await self.cache.delete(key)

    # --------------------------
    # 🔹 Контекстный менеджер
    # --------------------------
    def guard(self, token: str):
        """
        Асинхронный контекст, защищающий блок кода от повторного выполнения.

        Пример:
            async with idm.guard("approve:task:uuid"):
                await service.approve_task(task_id)
        """
        return _IdempotentGuard(self, token)


class _IdempotentGuard:
    """Контекстный менеджер для `async with idm.guard(...)`."""

    def __init__(self, manager: IdempotencyManager, token: str):
        self.manager = manager
        self.token = token

    async def __aenter__(self):
        await self.manager.register(self.token)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # Если выполнение неудачно — освобождаем ключ, чтобы можно было повторить
        if exc_type:
            await self.manager.release(self.token)
        # Если успешно — ключ остаётся до истечения TTL (доп. защита)
        return False  # не подавлять исключения


# --------------------------
# 🔸 Утилитарная функция
# --------------------------

async def ensure_idempotent(cache: CacheBackend, token: str, ttl: int = 60) -> None:
    """
    Простейшая функция для проверки/регистрации идемпотентности без контекстного менеджера.

    Пример:
        await ensure_idempotent(cache, f"deposit:{user_id}")
    """
    key = cache.build_key("idempotency", token)
    if await cache.exists(key):
        raise IdempotencyConflict(key)
    await cache.set(key, "locked", expire=ttl)
