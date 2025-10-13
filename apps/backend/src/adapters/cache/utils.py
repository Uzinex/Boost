"""
Uzinex Boost — Cache Utilities
==============================

Служебные функции для модулей кэширования:
- формирование ключей,
- сериализация/десериализация JSON,
- работа с TTL,
- генерация уникальных ключей и timestamp'ов.
"""

from __future__ import annotations

import json
import time
import hashlib
import uuid
from datetime import datetime, timedelta
from typing import Any, Optional, Union


# ----------------------------
# 🔹 Формирование ключей
# ----------------------------

def build_cache_key(namespace: str, *parts: Union[str, int]) -> str:
    """
    Формирует namespaced-ключ в едином стиле.
    Пример: build_cache_key('orders', 123, 'stats') -> 'orders:123:stats'
    """
    clean_parts = [str(p).strip() for p in parts if p is not None]
    return ":".join([namespace, *clean_parts])


def hash_key(value: str) -> str:
    """
    Возвращает короткий хэш (SHA1) строки — удобно для длинных URL или initData.
    """
    return hashlib.sha1(value.encode("utf-8")).hexdigest()[:24]


# ----------------------------
# 🔹 TTL и время
# ----------------------------

def ttl_to_seconds(ttl: Union[int, timedelta, None]) -> Optional[int]:
    """Преобразует timedelta или int в секунды."""
    if ttl is None:
        return None
    if isinstance(ttl, timedelta):
        return int(ttl.total_seconds())
    return int(ttl)


def is_expired(created_at: float, ttl: int) -> bool:
    """
    Проверяет, истекло ли время жизни ключа.
    :param created_at: UNIX timestamp (в секундах)
    :param ttl: время жизни в секундах
    """
    return (time.time() - created_at) > ttl


# ----------------------------
# 🔹 JSON сериализация
# ----------------------------

def to_json(value: Any) -> str:
    """Безопасная сериализация Python → JSON."""
    try:
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    except Exception as e:
        raise ValueError(f"JSON serialization error: {e}")


def from_json(value: Optional[str]) -> Any:
    """Безопасная десериализация JSON → Python."""
    if value is None:
        return None
    try:
        return json.loads(value)
    except Exception:
        return value


# ----------------------------
# 🔹 Генерация уникальных ключей / идентификаторов
# ----------------------------

def make_idempotency_key(prefix: str, unique_value: str) -> str:
    """
    Формирует уникальный Idempotency-Key для операции.
    Пример: make_idempotency_key('deposit', 'user123') -> 'deposit:1c9e3a8b...'
    """
    uid = uuid.uuid5(uuid.NAMESPACE_DNS, unique_value)
    return f"{prefix}:{uid.hex}"


def generate_timestamp_key(prefix: str) -> str:
    """
    Возвращает ключ с временной меткой — удобно для логов и аудита.
    Пример: generate_timestamp_key('proof') -> 'proof:20251012T001532'
    """
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%S")
    return f"{prefix}:{ts}"


# ----------------------------
# 🔹 Прочее
# ----------------------------

def safe_int(value: Any, default: int = 0) -> int:
    """Безопасное преобразование в int."""
    try:
        return int(value)
    except Exception:
        return default


def current_timestamp() -> int:
    """Возвращает текущий UNIX timestamp (в секундах)."""
    return int(time.time())
