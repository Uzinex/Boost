# syntax=docker/dockerfile:1.6

FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies required for asyncpg and build tools
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /tmp/requirements.txt
RUN python -m pip install --upgrade pip \
    && pip install --no-cache-dir -r /tmp/requirements.txt

# Copy application sources
COPY apps/backend /app/apps/backend
COPY .env.example /app/.env.example

ENV PYTHONPATH=/app/apps/backend/src

EXPOSE 8000

CMD ["uvicorn", "apps.backend.src.main:app", "--host", "0.0.0.0", "--port", "8000"]
