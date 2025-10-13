"""Inline keyboards used across the bot entry points."""

from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def main_menu_keyboard() -> InlineKeyboardMarkup:
    """Return the main navigation keyboard for bot users."""

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Пополнить баланс", callback_data="payments:deposit")],
            [
                InlineKeyboardButton(text="💰 Мой баланс", callback_data="balance:show"),
                InlineKeyboardButton(text="📈 Статистика", callback_data="start:stats"),
            ],
            [InlineKeyboardButton(text="💱 Курсы", callback_data="payments:rates")],
            [InlineKeyboardButton(text="ℹ️ Поддержка", callback_data="start:help")],
        ]
    )
