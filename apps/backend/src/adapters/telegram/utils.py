"""
Uzinex Boost — Telegram Utilities
=================================

Вспомогательные функции для Telegram-интеграции:
- форматирование и очистка текста;
- безопасные вызовы Telegram API;
- задержки между рассылками;
- логирование ошибок и успешных событий.

Используется всеми подсистемами Telegram адаптера.
"""

from __future__ import annotations

import asyncio
import logging
import html
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable, Optional

from .exceptions import TelegramAPIError


logger = logging.getLogger("uzinex.telegram.utils")


# ----------------------------
# 🔹 Форматирование текста
# ----------------------------

def escape_html(text: str) -> str:
    """Экранирует HTML-теги, чтобы не поломать форматирование Telegram."""
    if not text:
        return ""
    return html.escape(text)


def bold(text: str) -> str:
    """Возвращает жирный HTML-текст."""
    return f"<b>{escape_html(text)}</b>"


def italic(text: str) -> str:
    """Возвращает курсивный HTML-текст."""
    return f"<i>{escape_html(text)}</i>"


def monospace(text: str) -> str:
    """Оформляет текст в моноширинном стиле (код)."""
    return f"<code>{escape_html(text)}</code>"


def format_user_link(user_id: int, name: str) -> str:
    """Формирует HTML-ссылку на пользователя."""
    return f"<a href='tg://user?id={user_id}'>{escape_html(name)}</a>"


def format_currency(amount: float, currency: str = "UZT") -> str:
    """Форматирует валюту в человекочитаемом виде."""
    return f"{amount:,.2f} {currency}".replace(",", " ")


def timestamp() -> int:
    """Возвращает текущий Unix-timestamp."""
    return int(datetime.now(tz=timezone.utc).timestamp())


def utcnow() -> datetime:
    """Возвращает текущее UTC-время."""
    return datetime.now(tz=timezone.utc)


# ----------------------------
# 🔹 Асинхронные хелперы
# ----------------------------

async def safe_call(
    func: Callable[..., Awaitable[Any]],
    *args,
    retries: int = 2,
    delay: float = 1.0,
    **kwargs,
) -> Optional[Any]:
    """
    Безопасно вызывает асинхронную функцию Telegram API.
    В случае неудачи делает повторные попытки.

    :param func: асинхронная функция (например client.send_message)
    :param retries: количество попыток
    :param delay: задержка между попытками (сек)
    :return: результат вызова или None
    """
    for attempt in range(1, retries + 1):
        try:
            result = await func(*args, **kwargs)
            if attempt > 1:
                logger.info(f"[Retry OK] {func.__name__} succeeded on attempt {attempt}")
            return result
        except TelegramAPIError as e:
            logger.warning(f"[TelegramAPIError] {func.__name__}: {e}")
            if attempt == retries:
                logger.error(f"[Fail] {func.__name__} failed after {attempt} attempts.")
                return None
            await asyncio.sleep(delay)
        except Exception as e:
            logger.exception(f"[safe_call] Unexpected error in {func.__name__}: {e}")
            return None


async def async_sleep(seconds: float) -> None:
    """Асинхронная задержка (для рассылок и rate-limit)."""
    try:
        await asyncio.sleep(seconds)
    except asyncio.CancelledError:
        logger.warning("[async_sleep] Task cancelled during delay.")


# ----------------------------
# 🔹 Логирование
# ----------------------------

def log_event(event: str, user_id: Optional[int] = None, level: str = "info") -> None:
    """
    Централизованное логирование событий Telegram-интеграции.
    """
    msg = f"[Telegram] {event}"
    if user_id:
        msg += f" (user={user_id})"

    if level == "error":
        logger.error(msg)
    elif level == "warning":
        logger.warning(msg)
    else:
        logger.info(msg)


# ----------------------------
# 🔹 Форматирование уведомлений
# ----------------------------

def format_notification(title: str, text: str, emoji: str = "💬") -> str:
    """
    Формирует красиво отформатированное уведомление для пользователя.
    """
    return f"{emoji} <b>{escape_html(title)}</b>\n{text}"
