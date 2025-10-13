# syntax=docker/dockerfile:1.6

FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt /tmp/requirements.txt
RUN python -m pip install --upgrade pip \
    && pip install --no-cache-dir -r /tmp/requirements.txt

COPY apps/bot /app/apps/bot
COPY .env.example /app/.env.example

ENV PYTHONPATH=/app/apps/bot

CMD ["python", "apps/bot/app/main.py"]
