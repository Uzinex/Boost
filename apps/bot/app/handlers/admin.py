"""Administrative handlers restricted to privileged users."""

from __future__ import annotations

import logging
from typing import Iterable

from aiogram import Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message

from ..config import BotSettings
from ..service.api import APIClientError, BoostAPIClient


logger = logging.getLogger("boost.bot.handlers.admin")

router = Router(name="admin")


def _is_admin(message: Message, settings: BotSettings) -> bool:
    admin_ids: Iterable[int] = getattr(settings, "admin_ids", [])
    return bool(message.from_user) and message.from_user.id in set(admin_ids)


async def _ensure_admin(message: Message, settings: BotSettings) -> bool:
    if not _is_admin(message, settings):
        await message.answer("❌ Команда доступна только администраторам.")
        logger.warning("Unauthorized admin command from %s", message.from_user.id if message.from_user else "unknown")
        return False
    return True


@router.message(Command("admin"))
async def admin_menu(message: Message, settings: BotSettings) -> None:
    """Display available admin commands."""

    if not await _ensure_admin(message, settings):
        return

    text = (
        "👨‍💻 <b>Админ-панель Boost</b>\n\n"
        "Доступные команды:\n"
        "• /admin_stats — системная статистика.\n"
        "• /admin_health — проверка зависимостей.\n"
        "• /notify &lt;user_id&gt; &lt;текст&gt; — уведомление пользователю."
    )
    await message.answer(text)


@router.message(Command("admin_stats"))
async def admin_stats(
    message: Message,
    settings: BotSettings,
    api_client: BoostAPIClient,
) -> None:
    """Fetch and display system-level statistics."""

    if not await _ensure_admin(message, settings):
        return
    try:
        stats = await api_client.fetch_system_stats()
    except APIClientError as exc:
        logger.error("Failed to fetch system stats: %s", exc)
        await message.answer("⚠️ Не удалось получить системную статистику. Попробуйте позже.")
        return

    lines = ["📊 <b>Системная статистика</b>"]
    for key, title in (
        ("total_users", "Всего пользователей"),
        ("total_payments", "Всего заявок"),
        ("total_volume_uzt", "Оборот UZT"),
        ("active_orders", "Активных заказов"),
    ):
        value = stats.get(key)
        if value is None:
            continue
        formatted = f"{float(value):,.0f}" if isinstance(value, (int, float)) else value
        lines.append(f"• {title}: <b>{formatted}</b>")

    await message.answer("\n".join(lines))


@router.message(Command("admin_health"))
async def admin_health(
    message: Message,
    settings: BotSettings,
    api_client: BoostAPIClient,
) -> None:
    """Run backend health check via API."""

    if not await _ensure_admin(message, settings):
        return
    try:
        health = await api_client.health()
    except APIClientError as exc:
        logger.error("Failed to fetch health status: %s", exc)
        await message.answer("⚠️ Не удалось запросить состояние системы.")
        return

    details = health.get("details", {})
    lines = ["🩺 <b>Проверка системы</b>"]
    lines.append(f"Статус: <b>{'OK' if health.get('ok') else 'FAIL'}</b>")
    for component, status in details.items():
        lines.append(f"• {component.title()}: <b>{status}</b>")

    await message.answer("\n".join(lines))


@router.message(Command("notify"))
async def notify_user(
    message: Message,
    command: CommandObject,
    settings: BotSettings,
    api_client: BoostAPIClient,
) -> None:
    """Forward custom notification to a specific user."""

    if not await _ensure_admin(message, settings):
        return

    if not command.args:
        await message.answer("Использование: /notify &lt;telegram_id&gt; &lt;текст&gt;")
        return

    parts = command.args.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Нужно указать ID пользователя и текст сообщения.")
        return

    try:
        user_id = int(parts[0])
    except ValueError:
        await message.answer("ID пользователя должен быть числом.")
        return

    text = parts[1].strip()
    if not text:
        await message.answer("Текст сообщения не может быть пустым.")
        return

    try:
        await api_client.send_notification(user_id=user_id, text=text)
    except APIClientError as exc:
        logger.error("Failed to send notification via backend: %s", exc)
        await message.answer("⚠️ Не удалось отправить уведомление через backend.")
        return

    await message.answer("✅ Уведомление отправлено.")

