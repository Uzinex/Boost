"""
Uzinex Boost Core — Security Layer
===================================

Модуль безопасности:
- JWT-аутентификация (создание и валидация токенов)
- Проверка подписи Telegram WebApp initData
- Генерация и хэширование паролей (на будущее)
- Вспомогательные криптографические утилиты

Используется в API, Telegram WebApp и domain-сервисах.
"""

from __future__ import annotations
import os
import hmac
import hashlib
import base64
import logging
from datetime import datetime, timedelta
from typing import Any, Mapping, Optional, Dict

import jwt  # PyJWT
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from core.config import settings
from db.repositories.user_repository import UserRepository
from db.base import async_session_factory

logger = logging.getLogger("uzinex.core.security")


# -------------------------------------------------
# 🔹 JWT Token Management
# -------------------------------------------------

def create_session_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Создаёт JWT токен для сессии пользователя."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})

    token = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    logger.debug(f"[JWT] Created token for user {data.get('sub')} exp={expire.isoformat()}")
    return token


def decode_session_token(token: str) -> dict:
    """Проверяет и декодирует JWT токен."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


# -------------------------------------------------
# 🔹 Telegram WebApp initData Validation
# -------------------------------------------------

def validate_telegram_init_data(init_data: str, bot_token: Optional[str] = None) -> Dict[str, Any]:
    """Проверяет подлинность initData, полученного из Telegram WebApp."""
    if not init_data:
        raise HTTPException(status_code=400, detail="Missing init_data")

    bot_token = bot_token or settings.TELEGRAM_BOT_TOKEN
    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()

    data_check = []
    data_dict = {}
    for item in init_data.split("&"):
        if "=" not in item:
            continue
        key, value = item.split("=", 1)
        if key == "hash":
            received_hash = value
        else:
            data_check.append(f"{key}={value}")
            data_dict[key] = value

    check_string = "\n".join(sorted(data_check))
    calculated_hash = hmac.new(secret_key, check_string.encode(), hashlib.sha256).hexdigest()

    if calculated_hash != received_hash:
        logger.warning("[TelegramAuth] Invalid initData signature detected")
        raise HTTPException(status_code=403, detail="Invalid Telegram WebApp signature")

    logger.info(f"[TelegramAuth] Validated initData for user: {data_dict.get('user')}")
    return data_dict


# -------------------------------------------------
# 🔹 Password Hashing Utilities (future use)
# -------------------------------------------------

def hash_password(password: str) -> str:
    """Возвращает SHA256-хэш пароля (на будущее)."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def verify_password(password: str, hashed: str) -> bool:
    """Проверяет соответствие пароля и хэша."""
    return hmac.compare_digest(hash_password(password), hashed)


# -------------------------------------------------
# 🔹 Secure Random Generators
# -------------------------------------------------

def generate_secure_token(length: int = 32) -> str:
    """Генерирует безопасный base64 токен (для восстановления, приглашений и т.п.)."""
    return base64.urlsafe_b64encode(hashlib.sha256(os.urandom(length)).digest()).decode()[:length]


# -------------------------------------------------
# 🔹 Utility: User Session Payload Builder
# -------------------------------------------------

def build_user_payload(user_id: int, username: Optional[str] = None) -> dict:
    """Создаёт стандартный payload для JWT токена."""
    payload = {"sub": str(user_id)}
    if username:
        payload["username"] = username
    return payload


def create_user_session(user: Mapping[str, Any] | Any, expires_delta: Optional[timedelta] = None) -> str:
    """Создаёт JWT для пользователя (объект или dict)."""
    if isinstance(user, Mapping):
        user_id = user.get("id") or user.get("sub")
        username = user.get("username")
    else:
        user_id = getattr(user, "id", None)
        username = getattr(user, "username", None)

    if not user_id:
        raise ValueError("User object must provide an identifier")

    payload = build_user_payload(int(user_id), username=username)
    return create_session_token(payload, expires_delta)


# -------------------------------------------------
# 🔹 Dependency: get_current_user
# -------------------------------------------------

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Возвращает текущего пользователя из JWT токена."""
    try:
        payload = decode_session_token(token)
        user_id = int(payload.get("sub"))
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token payload")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

    async with async_session_factory() as session:
        repo = UserRepository(session)
        user = await repo.get_by_id(user_id)
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")

    return user
