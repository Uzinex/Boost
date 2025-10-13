"""
Uzinex Boost — Formatters
=========================

Модуль для форматирования чисел, валют, дат, имён и текстов.

Назначение:
-----------
Предоставляет единые функции для красивого вывода данных в API,
дашбордах, логах и аналитических отчётах.

Используется в:
- api.v1.responses
- domain.services.analytics
- utils.time_utils
"""

from __future__ import annotations
from datetime import datetime
import math
import locale

# Устанавливаем локаль (если доступна в системе)
try:
    locale.setlocale(locale.LC_ALL, "ru_RU.UTF-8")
except locale.Error:
    pass


# -------------------------------------------------
# 🔹 Форматирование чисел и валют
# -------------------------------------------------
def format_number(value: float, decimals: int = 0) -> str:
    """
    Форматирует число с разделителями тысяч.
    Пример: 15000 → '15 000'
    """
    try:
        return f"{value:,.{decimals}f}".replace(",", " ")
    except (ValueError, TypeError):
        return "0"


def format_currency(amount: float, currency: str = "UZT") -> str:
    """
    Форматирует сумму с валютным обозначением.
    Пример: 15000 → '15 000 UZT'
    """
    if amount is None:
        return "0 UZT"
    formatted = format_number(amount, 0)
    return f"{formatted} {currency}"


def compact_number(value: float) -> str:
    """
    Краткое форматирование больших чисел.
    Пример: 1200 → '1.2K', 2500000 → '2.5M'
    """
    if value is None:
        return "0"
    abs_val = abs(value)
    if abs_val >= 1_000_000_000:
        return f"{value / 1_000_000_000:.1f}B"
    elif abs_val >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    elif abs_val >= 1_000:
        return f"{value / 1_000:.1f}K"
    return f"{value:.0f}"


# -------------------------------------------------
# 🔹 Форматирование дат
# -------------------------------------------------
def format_date(dt: datetime, pattern: str = "%d %b %Y") -> str:
    """
    Форматирует дату в читаемый вид.
    Пример: datetime(2025,10,13) → '13 Oct 2025'
    """
    if not dt:
        return ""
    try:
        return dt.strftime(pattern)
    except Exception:
        return str(dt)


def format_datetime(dt: datetime, pattern: str = "%d %b %Y, %H:%M") -> str:
    """
    Форматирует дату и время.
    Пример: '13 Oct 2025, 18:45'
    """
    if not dt:
        return ""
    try:
        return dt.strftime(pattern)
    except Exception:
        return str(dt)


# -------------------------------------------------
# 🔹 Форматирование имён
# -------------------------------------------------
def short_name(full_name: str) -> str:
    """
    Преобразует полное имя в сокращённую форму.
    Пример: 'Feruz Dilov' → 'Feruz D.'
    """
    if not full_name or " " not in full_name:
        return full_name
    parts = full_name.strip().split()
    if len(parts) == 1:
        return parts[0]
    return f"{parts[0]} {parts[1][0].upper()}."


# -------------------------------------------------
# 🔹 Форматирование процентов и долей
# -------------------------------------------------
def format_percent(value: float, decimals: int = 1) -> str:
    """
    Форматирует значение как процент.
    Пример: 0.25 → '25.0%'
    """
    if value is None:
        return "0%"
    return f"{round(value * 100, decimals)}%"


def format_ratio(part: float, total: float, decimals: int = 1) -> str:
    """
    Вычисляет и форматирует отношение в процентах.
    Пример: 25, 100 → '25.0%'
    """
    if not total or total == 0:
        return "0%"
    return format_percent(part / total, decimals)


# -------------------------------------------------
# 🔹 Форматирование логов и аналитики
# -------------------------------------------------
def format_event(event_type: str, actor: str, value: str | float | None = None) -> str:
    """
    Унифицированное форматирование событий для логов.
    Пример: ('payment', 'User#5', '15 000 UZT') → '[PAYMENT] User#5 → 15 000 UZT'
    """
    value_str = f" → {value}" if value is not None else ""
    return f"[{event_type.upper()}] {actor}{value_str}"


def format_duration(seconds: int) -> str:
    """
    Форматирует продолжительность (в секундах) в человеко-читаемый вид.
    Пример: 3661 → '1h 1m 1s'
    """
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        m, s = divmod(seconds, 60)
        return f"{m}m {s}s"
    else:
        h, remainder = divmod(seconds, 3600)
        m, s = divmod(remainder, 60)
        return f"{h}h {m}m {s}s"
