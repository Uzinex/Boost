# ============================================================
# Uzinex Boost — Production Procfile (Railway Deployment)
# ============================================================
# Defines how Railway should run the FastAPI backend and bot.
# ============================================================

# Main backend API (FastAPI + Uvicorn)
web: cd apps/backend/src && uvicorn main:app --host 0.0.0.0 --port $PORT

# Optional: Telegram bot service (manual scale)
bot: cd apps/backend/bot/app && python main.py
