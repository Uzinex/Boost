"""
Uzinex Boost — Time Utilities
=============================

Модуль для работы со временем, датами и часовыми поясами.

Назначение:
-----------
- централизованная работа с UTC;
- преобразование времени в локальное (Tashkent, Asia/Tashkent);
- форматирование и вычисление временных интервалов;
- генерация меток для логов и аналитики.

Используется в:
- core.logging
- domain.services.*
- db.repositories.*
"""

from __future__ import annotations
from datetime import datetime, timedelta, timezone
import pytz


# -------------------------------------------------
# 🔹 Базовые константы
# -------------------------------------------------
UZBEK_TZ = pytz.timezone("Asia/Tashkent")
ISO_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
DATE_FORMAT = "%Y-%m-%d"
TIME_FORMAT = "%H:%M:%S"


# -------------------------------------------------
# 🔹 Текущее время
# -------------------------------------------------
def utc_now() -> datetime:
    """
    Возвращает текущее время в UTC.
    """
    return datetime.now(timezone.utc)


def now_tashkent() -> datetime:
    """
    Возвращает текущее время по часовому поясу Узбекистана.
    """
    return datetime.now(UZBEK_TZ)


# -------------------------------------------------
# 🔹 Форматирование
# -------------------------------------------------
def format_iso(dt: datetime) -> str:
    """
    Преобразует дату в ISO 8601 формат (UTC).
    """
    if not dt:
        return ""
    return dt.astimezone(timezone.utc).strftime(ISO_FORMAT)


def format_date(dt: datetime) -> str:
    """
    Возвращает дату в формате YYYY-MM-DD.
    """
    if not dt:
        return ""
    return dt.strftime(DATE_FORMAT)


def format_time(dt: datetime) -> str:
    """
    Возвращает время в формате HH:MM:SS.
    """
    if not dt:
        return ""
    return dt.strftime(TIME_FORMAT)


# -------------------------------------------------
# 🔹 Интервалы времени
# -------------------------------------------------
def format_timedelta(delta: timedelta) -> str:
    """
    Возвращает человеко-читаемое представление интервала.
    Пример: "2h 15m", "1d 3h", "45s".
    """
    if not delta:
        return "0s"

    seconds = int(delta.total_seconds())
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)

    parts = []
    if days:
        parts.append(f"{days}d")
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    if seconds or not parts:
        parts.append(f"{seconds}s")

    return " ".join(parts)


def humanize_datetime(dt: datetime) -> str:
    """
    Возвращает разницу между временем и сейчас в человеко-читаемом виде.
    Пример: "2 hours ago", "3 days ago", "just now".
    """
    if not dt:
        return "unknown"

    delta = utc_now() - dt.replace(tzinfo=timezone.utc)
    seconds = delta.total_seconds()

    if seconds < 60:
        return "just now"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    elif seconds < 86400:
        hours = int(seconds // 3600)
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif seconds < 2592000:
        days = int(seconds // 86400)
        return f"{days} day{'s' if days != 1 else ''} ago"
    else:
        months = int(seconds // 2592000)
        return f"{months} month{'s' if months != 1 else ''} ago"


# -------------------------------------------------
# 🔹 Конвертация между часовыми поясами
# -------------------------------------------------
def to_local_time(dt: datetime, tz: str = "Asia/Tashkent") -> datetime:
    """
    Конвертирует время UTC в локальный часовой пояс.
    """
    if not dt:
        return None
    local_tz = pytz.timezone(tz)
    return dt.astimezone(local_tz)


def to_utc(dt: datetime, tz: str = "Asia/Tashkent") -> datetime:
    """
    Конвертирует локальное время в UTC.
    """
    if not dt:
        return None
    local_tz = pytz.timezone(tz)
    return local_tz.localize(dt).astimezone(pytz.utc)
