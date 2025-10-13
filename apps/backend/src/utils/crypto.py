"""
Uzinex Boost — Crypto Utilities
===============================

Модуль для криптографических операций:
- хэширование и проверка паролей (bcrypt);
- создание и расшифровка JWT-токенов;
- генерация безопасных токенов и ключей;
- цифровые подписи и безопасное сравнение.

Используется в:
- core.security
- domain.services.user_service
- api.v1.auth
"""

import os
import jwt
import bcrypt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

# -------------------------------------------------
# 🔹 Константы безопасности
# -------------------------------------------------
JWT_SECRET = os.getenv("JWT_SECRET", "UZINEX_SUPER_SECRET_KEY")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = 48  # Срок действия токена по умолчанию


# -------------------------------------------------
# 🔹 Пароли
# -------------------------------------------------
def hash_password(password: str) -> str:
    """
    Создаёт bcrypt-хэш пароля.
    """
    if not password:
        raise ValueError("Password cannot be empty")
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    """
    Проверяет соответствие пароля и хэша.
    """
    if not password or not hashed:
        return False
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


# -------------------------------------------------
# 🔹 JWT токены
# -------------------------------------------------
def create_jwt(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None,
    secret: Optional[str] = None,
) -> str:
    """
    Создаёт JWT-токен на основе данных пользователя.
    """
    expire = datetime.utcnow() + (expires_delta or timedelta(hours=JWT_EXPIRE_HOURS))
    payload = {**data, "exp": expire, "iat": datetime.utcnow()}
    token = jwt.encode(payload, secret or JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token


def decode_jwt(token: str, secret: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Расшифровывает JWT и возвращает полезную нагрузку.
    """
    try:
        payload = jwt.decode(token, secret or JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


# -------------------------------------------------
# 🔹 Безопасные токены и подписи
# -------------------------------------------------
def generate_secure_token(length: int = 32) -> str:
    """
    Генерирует безопасный случайный токен.
    """
    return os.urandom(length).hex()


def compare_secure(a: str, b: str) -> bool:
    """
    Безопасное сравнение строк (устойчиво к тайминг-атакам).
    """
    if not a or not b:
        return False
    if len(a) != len(b):
        return False

    result = 0
    for x, y in zip(a.encode(), b.encode()):
        result |= x ^ y
    return result == 0
