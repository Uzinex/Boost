"""
Uzinex Boost — Cache Backend Base
=================================

Абстрактный слой кэш-хранилища.
Определяет интерфейс, которому должны соответствовать конкретные реализации,
например RedisCache, MemoryCache (для тестов) и т.п.

Используется в доменных сервисах для:
- rate-limit проверки,
- idempotency защиты,
- временного хранения заданий, профилей, статистики.
"""

from __future__ import annotations

import abc
import json
import asyncio
from datetime import timedelta
from typing import Any, Optional, Union


class CacheBackend(abc.ABC):
    """
    Абстрактный базовый класс для реализации асинхронных кэш-бэкендов.
    """

    def __init__(self, namespace: str = "uzinex_boost"):
        self.namespace = namespace

    # ---------------------------
    # 🔹 Основные операции
    # ---------------------------
    @abc.abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Возвращает значение по ключу (или None, если нет)."""

    @abc.abstractmethod
    async def set(self, key: str, value: Any, expire: Optional[int] = None) -> bool:
        """Сохраняет значение по ключу (опционально TTL в секундах)."""

    @abc.abstractmethod
    async def delete(self, key: str) -> int:
        """Удаляет ключ (возвращает кол-во удалённых записей)."""

    @abc.abstractmethod
    async def exists(self, key: str) -> bool:
        """Проверяет существование ключа."""

    @abc.abstractmethod
    async def incr(self, key: str, amount: int = 1, expire: Optional[int] = None) -> int:
        """Инкрементирует значение счётчика (используется для rate-limit)."""

    @abc.abstractmethod
    async def expire(self, key: str, seconds: int) -> bool:
        """Устанавливает TTL для ключа."""

    @abc.abstractmethod
    async def close(self) -> None:
        """Закрывает соединение с хранилищем."""

    # ---------------------------
    # 🔹 Вспомогательные методы
    # ---------------------------

    def build_key(self, *parts: Union[str, int]) -> str:
        """
        Формирует namespaced-ключ.
        Пример: build_key('user', 123, 'profile') -> 'uzinex_boost:user:123:profile'
        """
        joined = ":".join(str(p) for p in parts)
        return f"{self.namespace}:{joined}"

    @staticmethod
    def to_json(value: Any) -> str:
        """Сериализация Python-объекта в JSON."""
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))

    @staticmethod
    def from_json(value: Optional[str]) -> Any:
        """Десериализация JSON в Python-объект."""
        if value is None:
            return None
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value

    @staticmethod
    def ttl(seconds: Union[int, timedelta, None]) -> Optional[int]:
        """Преобразует timedelta или int в целое значение TTL."""
        if seconds is None:
            return None
        if isinstance(seconds, timedelta):
            return int(seconds.total_seconds())
        return int(seconds)

    # ---------------------------
    # 🔹 Контекстный менеджер
    # ---------------------------
    async def __aenter__(self) -> "CacheBackend":
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


# ---------------------------
# 🔸 Простая in-memory реализация (для тестов)
# ---------------------------

class MemoryCache(CacheBackend):
    """
    Временная реализация кэша в памяти, используется для unit-тестов.
    """

    def __init__(self):
        super().__init__(namespace="memory")
        self._store: dict[str, Any] = {}
        self._ttl: dict[str, float] = {}
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Optional[Any]:
        async with self._lock:
            if key in self._ttl and self._ttl[key] < asyncio.get_event_loop().time():
                # TTL истёк
                await self.delete(key)
                return None
            return self._store.get(key)

    async def set(self, key: str, value: Any, expire: Optional[int] = None) -> bool:
        async with self._lock:
            self._store[key] = value
            if expire:
                self._ttl[key] = asyncio.get_event_loop().time() + expire
            return True

    async def delete(self, key: str) -> int:
        async with self._lock:
            existed = key in self._store
            self._store.pop(key, None)
            self._ttl.pop(key, None)
            return int(existed)

    async def exists(self, key: str) -> bool:
        async with self._lock:
            return key in self._store

    async def incr(self, key: str, amount: int = 1, expire: Optional[int] = None) -> int:
        async with self._lock:
            current = int(self._store.get(key, 0)) + amount
            self._store[key] = current
            if expire:
                self._ttl[key] = asyncio.get_event_loop().time() + expire
            return current

    async def expire(self, key: str, seconds: int) -> bool:
        async with self._lock:
            if key not in self._store:
                return False
            self._ttl[key] = asyncio.get_event_loop().time() + seconds
            return True

    async def close(self) -> None:
        async with self._lock:
            self._store.clear()
            self._ttl.clear()
