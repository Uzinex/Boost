"""
Uzinex Boost — Telegram Notifier
================================

Модуль для отправки системных уведомлений пользователям и администраторам.

Задачи:
- централизовать логику уведомлений Telegram;
- предоставлять простой интерфейс send_notification();
- обеспечивать обработку ошибок и форматирование сообщений.

Используется сервисами Boost (например, Payments, Orders, Balance)
для информирования пользователей о событиях.
"""

from __future__ import annotations

import logging
from typing import Optional, Dict, Any

from .client import TelegramClient
from .exceptions import TelegramMessageError, TelegramUserNotFound, TelegramAPIError


logger = logging.getLogger("uzinex.telegram.notifier")


# ----------------------------
# 🔹 Основная функция уведомления
# ----------------------------

async def send_notification(
    client: TelegramClient,
    user_id: int | str,
    text: str,
    *,
    message_type: str = "info",
    photo_url: Optional[str] = None,
    parse_mode: str = "HTML",
    reply_markup: Optional[Dict[str, Any]] = None,
) -> bool:
    """
    Отправляет уведомление пользователю или админу.

    :param client: экземпляр TelegramClient
    :param user_id: Telegram ID получателя
    :param text: текст уведомления
    :param message_type: тип сообщения ("info", "success", "error", "system")
    :param photo_url: опциональная ссылка на изображение
    :param parse_mode: форматирование текста (HTML / Markdown)
    :param reply_markup: inline или reply-клавиатура
    :return: bool — успешно ли отправлено
    """

    prefix_map = {
        "info": "ℹ️",
        "success": "✅",
        "error": "❌",
        "system": "⚙️",
    }

    emoji = prefix_map.get(message_type, "💬")
    message_text = f"{emoji} {text}"

    try:
        if photo_url:
            await client.send_photo(chat_id=user_id, photo_url=photo_url, caption=message_text, parse_mode=parse_mode)
        else:
            await client.send_message(chat_id=user_id, text=message_text, parse_mode=parse_mode, reply_markup=reply_markup)

        logger.info(f"[Notifier] Sent {message_type.upper()} to {user_id}: {text[:80]}")
        return True

    except TelegramAPIError as e:
        logger.error(f"[Notifier] Telegram API error for {user_id}: {e}")
        raise TelegramMessageError(f"Failed to send message: {e}") from e

    except Exception as e:
        logger.exception(f"[Notifier] Unexpected error while sending message to {user_id}: {e}")
        raise TelegramUserNotFound(f"User {user_id} not found or message failed") from e


# ----------------------------
# 🔹 Групповые уведомления
# ----------------------------

async def broadcast(
    client: TelegramClient,
    user_ids: list[int | str],
    text: str,
    *,
    message_type: str = "info",
    chunk_size: int = 20,
) -> int:
    """
    Рассылает уведомление нескольким пользователям (batch).
    Возвращает количество успешно доставленных сообщений.
    """
    success = 0
    for i, uid in enumerate(user_ids, start=1):
        try:
            await send_notification(client, uid, text, message_type=message_type)
            success += 1
        except Exception as e:
            logger.warning(f"[Notifier] Failed to deliver to {uid}: {e}")

        if i % chunk_size == 0:
            logger.info(f"[Notifier] Sent to {i} users (current batch size {chunk_size})")

    logger.info(f"[Notifier] Broadcast completed: {success}/{len(user_ids)} delivered.")
    return success


# ----------------------------
# 🔹 Админ-уведомления
# ----------------------------

async def notify_admins(
    client: TelegramClient,
    admin_ids: list[int | str],
    text: str,
    *,
    alert: bool = False,
) -> None:
    """
    Отправляет сообщение всем администраторам.
    """
    prefix = "🚨" if alert else "📢"
    message = f"{prefix} {text}"

    for admin_id in admin_ids:
        try:
            await client.send_message(chat_id=admin_id, text=message)
        except Exception as e:
            logger.warning(f"[Notifier] Failed to notify admin {admin_id}: {e}")
