"""
Uzinex Boost — Payment Utilities
================================

Служебные функции для платёжных адаптеров:
- генерация invoice_id, токенов и сигнатур;
- проверка HMAC-подписи webhook’ов;
- форматирование и нормализация сумм;
- timestamp и валидация времени.
"""

from __future__ import annotations

import hashlib
import hmac
import uuid
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Union


# ----------------------------
# 🔹 Идентификаторы / токены
# ----------------------------

def generate_invoice_id(prefix: str = "inv") -> str:
    """
    Генерирует уникальный invoice_id в формате inv_xxx-uuid.
    """
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def generate_txn_id(prefix: str = "txn") -> str:
    """Создаёт короткий идентификатор транзакции."""
    return f"{prefix}_{uuid.uuid4().hex[:10]}"


def generate_secret_token(length: int = 24) -> str:
    """Генерирует случайный безопасный токен (hex)."""
    return uuid.uuid4().hex[:length]


# ----------------------------
# 🔹 Подписи и хэши
# ----------------------------

def compute_hmac_sha256(secret: str, message: str) -> str:
    """
    Вычисляет HMAC SHA256-подпись для строки.
    Используется при проверке callback-запросов.
    """
    return hmac.new(secret.encode(), message.encode(), hashlib.sha256).hexdigest()


def verify_signature(secret: str, message: str, signature: str) -> bool:
    """
    Проверяет корректность подписи (защита от подмены).
    """
    try:
        expected = compute_hmac_sha256(secret, message)
        return hmac.compare_digest(expected, signature)
    except Exception:
        return False


def md5_hash(data: str) -> str:
    """Возвращает MD5-хэш строки (используется некоторыми API, например Click)."""
    return hashlib.md5(data.encode()).hexdigest()


# ----------------------------
# 🔹 Суммы и валюты
# ----------------------------

def normalize_amount(value: Union[int, float, str]) -> float:
    """Безопасно преобразует сумму в float (2 знака)."""
    try:
        return round(float(value), 2)
    except Exception:
        return 0.0


def uzs_to_uzt(amount_uzs: float, rate: float = 75.0) -> float:
    """
    Переводит сумму из сумов в UZT (виртуальную валюту).
    Пример: 7500 сум → 100 UZT при rate=75.
    """
    return round(amount_uzs / rate, 2)


def uzt_to_uzs(amount_uzt: float, rate: float = 75.0) -> float:
    """Обратное преобразование (UZT → сумы)."""
    return round(amount_uzt * rate, 2)


def format_currency(value: float, currency: str = "UZS") -> str:
    """Форматирует сумму для вывода: 12 345.00 UZS."""
    return f"{value:,.2f} {currency}".replace(",", " ")


# ----------------------------
# 🔹 Время и timestamp
# ----------------------------

def now_utc() -> datetime:
    """Возвращает текущее время в UTC."""
    return datetime.now(timezone.utc)


def timestamp() -> int:
    """Возвращает UNIX timestamp (в секундах)."""
    return int(time.time())


def isoformat(dt: Optional[datetime] = None) -> str:
    """Возвращает ISO-строку (UTC)."""
    return (dt or now_utc()).isoformat()


# ----------------------------
# 🔹 Callback-валидаторы
# ----------------------------

def validate_callback_fields(data: Dict[str, Any], required: list[str]) -> bool:
    """
    Проверяет наличие обязательных полей в callback-запросе.
    Возвращает True, если все есть.
    """
    return all(field in data for field in required)


def build_signature_payload(data: Dict[str, Any], fields: list[str]) -> str:
    """
    Собирает строку для подписи из указанных полей (в порядке).
    Пример:
        fields = ["merchant_id", "amount", "transaction_id"]
        → "123|15000|tx_abc"
    """
    return "|".join(str(data.get(f, "")) for f in fields)


# ----------------------------
# 🔹 Разное
# ----------------------------

def safe_int(value: Any, default: int = 0) -> int:
    """Безопасное преобразование в int."""
    try:
        return int(value)
    except Exception:
        return default


def safe_str(value: Any, default: str = "") -> str:
    """Безопасное преобразование в строку."""
    if value is None:
        return default
    return str(value)
