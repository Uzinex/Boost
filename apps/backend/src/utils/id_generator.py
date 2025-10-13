"""
Uzinex Boost — ID Generator
===========================

Модуль для генерации уникальных идентификаторов, токенов и реферальных кодов.

Назначение:
-----------
Обеспечивает безопасную и стандартизированную генерацию ID для:
- пользователей, заказов, задач, платежей;
- реферальных и приглашённых кодов;
- внутренних системных ключей и токенов.

Используется в:
- domain.services.*
- core.security
- db.models.*
"""

import uuid
import random
import string
import secrets
import hashlib
from datetime import datetime


# -------------------------------------------------
# 🔹 UUID и короткие ID
# -------------------------------------------------
def generate_uuid() -> str:
    """
    Генерирует UUIDv4.
    Пример: 'a4f29d4e-ff12-43b3-bc60-1ad57b5cb6d3'
    """
    return str(uuid.uuid4())


def generate_short_id(prefix: str = "UZ") -> str:
    """
    Генерирует короткий читаемый ID (8–10 символов).
    Пример: 'UZ-8F9C3D1A'
    """
    base = uuid.uuid4().hex[:8].upper()
    return f"{prefix}-{base}"


# -------------------------------------------------
# 🔹 Реферальные и инвайт-коды
# -------------------------------------------------
def generate_ref_code(length: int = 8) -> str:
    """
    Генерирует реферальный код из латинских символов и цифр.
    Пример: 'NEXR8Z2Q'
    """
    alphabet = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def generate_invite_token(length: int = 32) -> str:
    """
    Генерирует безопасный токен приглашения / авторизации.
    Пример: 'd2f8ac9b3e45a8c7b123...'
    """
    return secrets.token_hex(length // 2)


# -------------------------------------------------
# 🔹 Хэш-идентификаторы
# -------------------------------------------------
def generate_hash_id(value: str) -> str:
    """
    Создаёт хэш-идентификатор на основе SHA256.
    Используется для однозначного вычисления ID из строки.
    """
    if not value:
        value = str(datetime.utcnow().timestamp())
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


# -------------------------------------------------
# 🔹 Короткий код подтверждения
# -------------------------------------------------
def generate_numeric_code(length: int = 6) -> str:
    """
    Генерирует числовой код (например, для SMS или e-mail верификации).
    Пример: '482193'
    """
    return "".join(random.choices(string.digits, k=length))


# -------------------------------------------------
# 🔹 Комбинированный ключ
# -------------------------------------------------
def generate_composite_key(user_id: int, prefix: str = "KEY") -> str:
    """
    Генерирует уникальный ключ, комбинируя ID пользователя и текущий timestamp.
    Пример: 'KEY-1-1734109212'
    """
    timestamp = int(datetime.utcnow().timestamp())
    return f"{prefix}-{user_id}-{timestamp}"
