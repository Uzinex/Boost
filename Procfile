# ============================================================
# Uzinex Boost — Production Procfile (Railway Deployment)
# ============================================================
# This file defines process types for the Uzinex Boost monorepo.
# Railway will detect it automatically and start the backend service.
# ============================================================

# Backend API (FastAPI + Uvicorn)
web: cd apps/backend/src && uvicorn main:app --host 0.0.0.0 --port $PORT

# Optional: run Telegram bot (manual scale, if needed)
bot: cd apps/backend/bot/app && python main.py
