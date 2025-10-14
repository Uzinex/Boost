"""
Uzinex Boost — Redis Cache Backend
==================================

Асинхронная реализация CacheBackend с использованием Redis.
"""

from __future__ import annotations
import asyncio
import logging
from typing import Any, Optional
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

    # -------------------------------------------------
    # 🔹 Подключение
    # -------------------------------------------------
    async def connect(self) -> None:
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
                await self._client.ping()
                logger.info(f"✅ Connected to Redis ({self._url or f'{self._host}:{self._port}'})")
            except Exception as e:
                raise CacheConnectionError(f"Cannot connect to Redis: {e}")

    async def ensure_connection(self) -> redis.Redis:
        if self._client is None:
            await self.connect()
        else:
            try:
                await self._client.ping()
            except Exception:
                await self.reconnect()
        return self._client

    async def reconnect(self) -> None:
        for attempt in range(1, self._reconnect_attempts + 1):
            try:
                await self.connect()
                return
            except CacheConnectionError:
                logger.warning(f"Reconnect attempt {attempt} failed")
                await asyncio.sleep(self._reconnect_delay)
        raise CacheConnectionError("Unable to reconnect to Redis after retries.")

    # -------------------------------------------------
    # 🔹 Ping (для healthcheck)
    # -------------------------------------------------
    async def ping(self) -> bool:
        """Проверяет соединение с Redis."""
        try:
            client = await self.ensure_connection()
            pong = await client.ping()
            return bool(pong)
        except Exception as e:
            logger.error(f"Redis ping failed: {e}")
            return False

    # -------------------------------------------------
    # 🔹 CRUD операции
    # -------------------------------------------------
    async def get(self, key: str) -> Optional[Any]:
        client = await self.ensure_connection()
        try:
            return await client.get(key)
        except Exception as e:
            raise CacheInternalError(f"GET failed for {key}", cause=e)
