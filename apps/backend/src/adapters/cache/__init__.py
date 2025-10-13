"""
Uzinex Boost — Cache Adapter Package
====================================

Пакет `adapters.cache` реализует инфраструктурный слой кэширования.
Он используется для:
- rate-limit и антиспама,
- кэширования пользовательских данных и статистики,
- хранения idempotency-ключей и временных состояний задач.

Основная реализация — Redis (через aioredis).
Интерфейс стандартизирован через `CacheBackend` в base.py.
"""

from typing import Optional
from .base import CacheBackend
from .redis_cache import RedisCache
from .exceptions import CacheConnectionError, RateLimitExceeded

# Глобальный экземпляр кэша (Singleton)
_cache_instance: Optional[CacheBackend] = None


def init_cache(**kwargs) -> CacheBackend:
    """
    Инициализация глобального экземпляра кэша.
    Обычно вызывается один раз при старте FastAPI-приложения (в startup event).

    Пример:
        from adapters.cache import init_cache
        cache = init_cache(url=settings.REDIS_URL)

    :param kwargs: параметры подключения (url, host, port, db, password и т.д.)
    :return: объект CacheBackend
    """
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = RedisCache(**kwargs)
    return _cache_instance


def get_cache() -> CacheBackend:
    """
    Возвращает текущий активный экземпляр CacheBackend.
    Если кэш не инициализирован — выбрасывает CacheConnectionError.
    """
    if _cache_instance is None:
        raise CacheConnectionError("Cache backend not initialized. Call init_cache() first.")
    return _cache_instance


async def close_cache() -> None:
    """
    Безопасное завершение работы кэша (закрытие соединения Redis).
    Рекомендуется вызывать в FastAPI shutdown event.
    """
    global _cache_instance
    if _cache_instance:
        await _cache_instance.close()
        _cache_instance = None


__all__ = [
    "init_cache",
    "get_cache",
    "close_cache",
    "CacheBackend",
    "CacheConnectionError",
    "RateLimitExceeded",
]
