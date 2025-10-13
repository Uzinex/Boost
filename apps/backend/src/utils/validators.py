"""
Uzinex Boost — Validators
=========================

Модуль для универсальной валидации пользовательских данных.

Назначение:
-----------
Содержит функции для проверки:
- формата email и username;
- длины и сложности паролей;
- числовых значений (сумм, процентов);
- номеров телефонов и идентификаторов.

Используется в:
- api.v1.schemas
- domain.services.user_service
- core.security
"""

import re
from typing import Optional


# -------------------------------------------------
# 🔹 Email
# -------------------------------------------------
EMAIL_REGEX = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")


def validate_email(email: str) -> bool:
    """
    Проверяет корректность email-адреса.
    """
    if not email or len(email) > 255:
        return False
    return bool(EMAIL_REGEX.match(email))


# -------------------------------------------------
# 🔹 Username
# -------------------------------------------------
USERNAME_REGEX = re.compile(r"^[A-Za-z0-9_.-]{3,30}$")


def validate_username(username: str) -> bool:
    """
    Проверяет имя пользователя:
    - от 3 до 30 символов,
    - допустимы латинские буквы, цифры, '_', '-', '.'.
    """
    if not username:
        return False
    return bool(USERNAME_REGEX.match(username))


# -------------------------------------------------
# 🔹 Пароль
# -------------------------------------------------
PASSWORD_REGEX = re.compile(
    r"^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[!@#$%^&*()_+\-=\[\]{};':\",.<>\/?]).{8,64}$"
)


def validate_password(password: str) -> bool:
    """
    Проверяет сложность пароля:
    - минимум 8 символов;
    - содержит заглавные, строчные, цифры и спецсимволы.
    """
    if not password:
        return False
    return bool(PASSWORD_REGEX.match(password))


# -------------------------------------------------
# 🔹 Суммы и числа
# -------------------------------------------------
def validate_amount(amount: Optional[float]) -> bool:
    """
    Проверяет корректность суммы (UZT):
    - число положительное,
    - не превышает 1 млрд.
    """
    if amount is None:
        return False
    try:
        return 0 < float(amount) <= 1_000_000_000
    except (ValueError, TypeError):
        return False


# -------------------------------------------------
# 🔹 Телефон
# -------------------------------------------------
PHONE_REGEX = re.compile(r"^\+998\d{9}$")  # Формат Узбекистана


def validate_phone(phone: str) -> bool:
    """
    Проверяет номер телефона (UZ формат):
    +998 и 9 цифр.
    """
    if not phone:
        return False
    return bool(PHONE_REGEX.match(phone))


# -------------------------------------------------
# 🔹 Идентификаторы
# -------------------------------------------------
def validate_id(value: Optional[int]) -> bool:
    """
    Проверяет, что ID — целое положительное число.
    """
    return isinstance(value, int) and value > 0


# -------------------------------------------------
# 🔹 Общие утилиты валидации
# -------------------------------------------------
def is_non_empty(value: Optional[str]) -> bool:
    """
    Проверяет, что строка не пуста и не состоит только из пробелов.
    """
    return bool(value and str(value).strip())


def validate_url(url: str) -> bool:
    """
    Проверяет корректность URL.
    """
    pattern = re.compile(
        r"^(https?:\/\/)?([A-Za-z0-9.-]+)\.([A-Za-z]{2,})([\/\w .-]*)*\/?$"
    )
    return bool(pattern.match(url))
