"""
Uzinex Boost — Redis Cache Backend
==================================

Асинхронная реализация CacheBackend с использованием Redis.

Основные функции:
- key/value операции (get/set/delete)
- TTL и инкременты
- надёжное соединение с авто-восстановлением
- базовый JSON-сериализатор
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Optional, Union

import redis.asyncio as redis

from .base import CacheBackend
from .exceptions import CacheConnectionError, CacheSerializationError, CacheInternalError


logger = logging.getLogger("uzinex.cache")


class RedisCache(CacheBackend):
    """Асинхронный Redis-кэш для Uzinex Boost."""

    def __init__(
        self,
        url: Optional[str] = None,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        namespace: str = "uzinex_boost",
        decode_responses: bool = True,
        reconnect_attempts: int = 3,
        reconnect_delay: float = 1.0,
    ):
        """
        :param url: redis://... приоритетнее, чем host/port
        :param reconnect_attempts: число попыток переподключения при сбое
        :param reconnect_delay: задержка между попытками
        """
        super().__init__(namespace)
        self._url = url
        self._host = host
        self._port = port
        self._db = db
        self._password = password
        self._decode_responses = decode_responses
        self._client: Optional[redis.Redis] = None
        self._lock = asyncio.Lock()
        self._reconnect_attempts = reconnect_attempts
        self._reconnect_delay = reconnect_delay

    # -----------------------------
    # 🔹 Подключение / отключение
    # -----------------------------

    async def connect(self) -> None:
        """Устанавливает соединение с Redis."""
        async with self._lock:
            try:
                if self._url:
                    self._client = redis.from_url(
                        self._url,
                        decode_responses=self._decode_responses,
                        encoding="utf-8",
                    )
                else:
                    self._client = redis.Redis(
                        host=self._host,
                        port=self._port,
                        db=self._db,
                        password=self._password,
                        decode_responses=self._decode_responses,
                        encoding="utf-8",
                    )
                # тестируем соединение
                await self._client.ping()
                logger.info("✅ Connected to Redis (%s)", self._url or f"{self._host}:{self._port}")
            except Exception as e:
                logger.error("❌ Failed to connect to Redis: %s", e)
                raise CacheConnectionError(f"Cannot connect to Redis: {e}")

    async def ensure_connection(self) -> redis.Redis:
        """Проверяет, что соединение живое; при необходимости переподключается."""
        if self._client is None:
            await self.connect()
        else:
            try:
                await self._client.ping()
            except Exception:
                logger.warning("Redis connection lost — reconnecting...")
                await self.reconnect()
        return self._client

    async def reconnect(self) -> None:
        """Пробует восстановить соединение несколько раз."""
        for attempt in range(1, self._reconnect_attempts + 1):
            try:
                await self.connect()
                return
            except CacheConnectionError:
                logger.warning("Reconnect attempt %d failed", attempt)
                await asyncio.sleep(self._reconnect_delay)
        raise CacheConnectionError("Unable to reconnect to Redis after retries.")

    async def close(self) -> None:
        """Закрывает соединение с Redis."""
        if self._client:
            try:
                await self._client.close()
                logger.info("🔒 Redis connection closed.")
            except Exception as e:
                logger.warning("Error closing Redis: %s", e)
            finally:
                self._client = None

    # -----------------------------
    # 🔹 CRUD операции
    # -----------------------------

    async def get(self, key: str) -> Optional[Any]:
        client = await self.ensure_connection()
        try:
            return await client.get(key)
        except Exception as e:
            raise CacheInternalError(f"GET failed for {key}", cause=e)

    async def set(self, key: str, value: Any, expire: Optional[int] = None) -> bool:
        client = await self.ensure_connection()
        try:
            if not isinstance(value, str):
                value = self.to_json(value)
            return await client.set(key, value, ex=self.ttl(expire))
        except TypeError as e:
            raise CacheSerializationError(f"Invalid type for key {key}", cause=e)
        except Exception as e:
            raise CacheInternalError(f"SET failed for {key}", cause=e)

    async def delete(self, key: str) -> int:
        client = await self.ensure_connection()
        try:
            return await client.delete(key)
        except Exception as e:
            raise CacheInternalError(f"DELETE failed for {key}", cause=e)

    async def exists(self, key: str) -> bool:
        client = await self.ensure_connection()
        try:
            return bool(await client.exists(key))
        except Exception as e:
            raise CacheInternalError(f"EXISTS failed for {key}", cause=e)

    async def incr(self, key: str, amount: int = 1, expire: Optional[int] = None) -> int:
        client = await self.ensure_connection()
        try:
            pipe = client.pipeline(transaction=True)
            pipe.incrby(key, amount)
            if expire:
                pipe.expire(key, self.ttl(expire))
            result = await pipe.execute()
            return int(result[0])
        except Exception as e:
            raise CacheInternalError(f"INCR failed for {key}", cause=e)

    async def expire(self, key: str, seconds: int) -> bool:
        client = await self.ensure_connection()
        try:
            return bool(await client.expire(key, seconds))
        except Exception as e:
            raise CacheInternalError(f"EXPIRE failed for {key}", cause=e)

    # -----------------------------
    # 🔹 Дополнительные методы
    # -----------------------------

    async def get_ttl(self, key: str) -> Optional[int]:
        """
        Возвращает оставшееся время жизни ключа (TTL в секундах).
        """
        client = await self.ensure_connection()
        try:
            ttl = await client.ttl(key)
            if ttl is None or ttl < 0:
                return None
            return int(ttl)
        except Exception:
            return None

    async def keys(self, pattern: str) -> list[str]:
        """Возвращает список ключей по шаблону."""
        client = await self.ensure_connection()
        try:
            return [str(k) for k in await client.keys(pattern)]
        except Exception as e:
            raise CacheInternalError(f"KEYS failed for pattern {pattern}", cause=e)

    async def flush(self) -> None:
        """Полная очистка Redis (только для DEV/TEST)."""
        client = await self.ensure_connection()
        try:
            await client.flushdb()
        except Exception as e:
            raise CacheInternalError("FLUSHDB failed", cause=e)
