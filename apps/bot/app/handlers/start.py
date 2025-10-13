"""Handlers for common user commands (/start, /help)."""

from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.types import CallbackQuery, Message

from ..service.api import APIClientError, BoostAPIClient
from ..keyboards import main_menu_keyboard


logger = logging.getLogger("boost.bot.handlers.start")

router = Router(name="common")


def _get_api_client(message: Message | CallbackQuery) -> BoostAPIClient:
    api_client = message.bot.get("api_client") if isinstance(message, Message) else message.message.bot.get("api_client")
    if not isinstance(api_client, BoostAPIClient):
        raise RuntimeError("BoostAPIClient is not configured for the bot instance")
    return api_client


@router.message(CommandStart())
async def cmd_start(message: Message, command: CommandObject | None = None) -> None:
    """Greet the user and show the main menu."""

    api_client = _get_api_client(message)
    user = message.from_user
    referral = command.args if command else None

    stats_text = ""
    try:
        stats = await api_client.fetch_public_stats()
    except APIClientError as exc:  # pragma: no cover - network errors are logged
        logger.warning("Failed to fetch public stats: %s", exc)
        stats = {}
    if stats:
        users = stats.get("total_users") or stats.get("users")
        total_paid = stats.get("total_paid_uzt") or stats.get("total_deposit_uzt")
        completed = stats.get("tasks_completed")
        stats_chunks = []
        if users is not None:
            stats_chunks.append(f"👥 Пользователей: <b>{users}</b>")
        if total_paid is not None:
            stats_chunks.append(f"💳 Пополнено: <b>{float(total_paid):,.0f} UZT</b>")
        if completed is not None:
            stats_chunks.append(f"✅ Выполнено задач: <b>{completed}</b>")
        if stats_chunks:
            stats_text = "\n".join(stats_chunks)

    greeting = [
        "👋 <b>Привет!</b>",
        "Это официальный бот платформы <b>Boost</b>.",
        "Здесь вы можете следить за балансом, пополнять счёт и получать уведомления.",
    ]

    if user and user.full_name:
        greeting.insert(0, f"👤 <b>{user.full_name}</b>")

    if stats_text:
        greeting.append("\n" + stats_text)

    if referral:
        greeting.append("\n🔗 Спасибо, что пришли по пригласительной ссылке! Код учтён.")

    await message.answer("\n".join(greeting), reply_markup=main_menu_keyboard())


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    """Provide a short help message."""

    help_text = (
        "ℹ️ <b>Как пользоваться ботом</b>\n\n"
        "• Используйте кнопки ниже, чтобы пополнить баланс или посмотреть статистику.\n"
        "• Для вопросов обращайтесь в службу поддержки: @boost_support.\n"
        "• Пополнения обрабатываются администраторами в течение 5–15 минут."
    )
    await message.answer(help_text, reply_markup=main_menu_keyboard())


@router.callback_query(F.data == "start:help")
async def cb_help(callback: CallbackQuery) -> None:
    """Handle inline request for help."""

    await callback.answer()
    await cmd_help(callback.message)


@router.callback_query(F.data == "start:stats")
async def cb_stats(callback: CallbackQuery) -> None:
    """Send fresh stats on demand."""

    await callback.answer()
    api_client = _get_api_client(callback)
    try:
        stats = await api_client.fetch_public_stats()
    except APIClientError as exc:
        logger.error("Failed to fetch stats via callback: %s", exc)
        await callback.message.answer("⚠️ Сейчас не получается получить статистику. Попробуйте позже.")
        return

    text_lines = ["📈 <b>Статистика Boost</b>"]
    for key, title in (
        ("total_users", "Всего пользователей"),
        ("active_orders", "Активных заказов"),
        ("tasks_completed", "Выполнено задач"),
        ("total_paid_uzt", "Пополнено UZT"),
    ):
        value = stats.get(key)
        if value is None:
            continue
        formatted = f"{float(value):,.0f}" if isinstance(value, (int, float)) else value
        text_lines.append(f"• {title}: <b>{formatted}</b>")

    await callback.message.answer("\n".join(text_lines))


@router.callback_query(F.data == "balance:show")
async def cb_balance(callback: CallbackQuery) -> None:
    """Show current balance fetched from backend."""

    await callback.answer()
    api_client = _get_api_client(callback)
    user = callback.from_user
    if not user:
        await callback.message.answer("Не удалось определить пользователя.")
        return

    try:
        balance = await api_client.fetch_balance(user.id)
    except APIClientError as exc:
        logger.error("Failed to fetch balance: %s", exc)
        await callback.message.answer("⚠️ Баланс временно недоступен. Попробуйте позже.")
        return

    if balance is None:
        await callback.message.answer("ℹ️ Баланс пока недоступен. Попробуйте позже.")
        return

    await callback.message.answer(f"💰 Ваш текущий баланс: <b>{balance:.2f} UZT</b>")
