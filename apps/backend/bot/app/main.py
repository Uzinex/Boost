"""
Uzinex Boost — Telegram Bot Entrypoint
======================================

Лёгкий Telegram бот на Aiogram 3.x,
используется для связи с WebApp и пользователей.
"""

import os
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, WebAppInfo

# ✅ токен из переменных окружения
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WEBAPP_URL = os.getenv("WEBAPP_URL", "https://boost-production-602a.up.railway.app")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# -----------------------------------------------------
# 🔹 Клавиатура с кнопкой WebApp
# -----------------------------------------------------
def build_main_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text="🚀 Open WebApp",
                    web_app=WebAppInfo(url=WEBAPP_URL)
                )
            ]
        ],
        resize_keyboard=True,
        input_field_placeholder="Нажми кнопку ниже 👇"
    )

# -----------------------------------------------------
# 🔹 Команда /start
# -----------------------------------------------------
@dp.message(F.text == "/start")
async def cmd_start(message: Message):
    kb = build_main_kb()
    await message.answer(
        "👋 Привет! Я бот <b>Uzinex Boost</b> 🚀\n\n"
        "💼 Через меня ты можешь выполнять задания, "
        "зарабатывать токены <b>UZT</b> и управлять балансом.\n\n"
        "Нажми кнопку ниже, чтобы открыть WebApp 👇",
        reply_markup=kb,
        parse_mode="HTML"
    )

# -----------------------------------------------------
# 🔹 Запуск бота
# -----------------------------------------------------
async def start_bot():
    print("🤖 Bot polling started...")
    await dp.start_polling(bot)
