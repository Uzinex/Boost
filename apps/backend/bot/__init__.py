from aiogram import Bot, Dispatcher
from core.config import settings

bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
dp = Dispatcher()
