from aiogram import Bot, Dispatcher

from aiogram.enums import ParseMode

from core.config import settings

from bot.app.service.bot_service import router as bot_router


dp = Dispatcher()
dp.include_router(bot_router)
