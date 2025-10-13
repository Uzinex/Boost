# ============================================================
# Uzinex Boost — Project Makefile
# ============================================================
# Provides a unified developer experience for the monorepo.
# Key targets:
#   make install        Install Python dependencies
#   make format         Format code with Black + isort
#   make lint           Run static analysis (flake8 + mypy)
#   make test           Run pytest test-suite
#   make run-backend    Start FastAPI with autoreload
#   make run-bot        Run Telegram bot in polling mode
#   make migrate        Apply database migrations
#   make docker-up      Start full stack via docker compose
# ============================================================

PYTHON ?= python3
PIP ?= $(PYTHON) -m pip
ENV_FILE ?= .env
COMPOSE ?= docker compose
COMPOSE_FILE ?= infra/docker-compose.yml
ALEMBIC ?= alembic
BACKEND_APP ?= apps.backend.src.main:app
BACKEND_PATH ?= apps/backend/src
BOT_PATH ?= apps/bot/app

.PHONY: install install-dev format lint lint-mypy lint-flake8 test run-backend run-bot migrate revision docker-build docker-up docker-down docker-logs docker-ps clean __ensure-env

## Install runtime + tooling dependencies using pip
install: __ensure-env
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

## Optional: install development dependencies only (alias to install)
install-dev: install

## Format Python sources with Black and isort
format:
	$(PYTHON) -m black $(BACKEND_PATH) $(BOT_PATH)
	$(PYTHON) -m isort $(BACKEND_PATH) $(BOT_PATH)

## Run both flake8 and mypy linters
lint: lint-flake8 lint-mypy

lint-flake8:
	$(PYTHON) -m flake8 $(BACKEND_PATH) $(BOT_PATH)

lint-mypy:
	$(PYTHON) -m mypy $(BACKEND_PATH)

## Execute pytest suite (backend focus)
test:
	PYTHONPATH=$(BACKEND_PATH) $(PYTHON) -m pytest apps/backend/tests

## Launch FastAPI backend locally with auto-reload
run-backend: __ensure-env
	PYTHONPATH=$(BACKEND_PATH) $(PYTHON) -m uvicorn $(BACKEND_APP) --host 0.0.0.0 --port 8000 --reload

## Launch Telegram bot locally (polling mode)
run-bot: __ensure-env
	PYTHONPATH=$(BOT_PATH) $(PYTHON) $(BOT_PATH)/main.py

## Run Alembic migrations against configured database
migrate: __ensure-env
	PYTHONPATH=$(BACKEND_PATH) $(ALEMBIC) -c apps/backend/alembic.ini upgrade head

## Create a new Alembic revision (usage: make revision message="add users")
revision: __ensure-env
	PYTHONPATH=$(BACKEND_PATH) $(ALEMBIC) -c apps/backend/alembic.ini revision --autogenerate -m "$(message)"

## Build Docker images for all services
docker-build:
	$(COMPOSE) -f $(COMPOSE_FILE) --env-file $(ENV_FILE) build

## Start full stack using Docker Compose (detached)
docker-up: __ensure-env
	$(COMPOSE) -f $(COMPOSE_FILE) --env-file $(ENV_FILE) up -d

## Stop and remove Docker Compose resources
docker-down:
	$(COMPOSE) -f $(COMPOSE_FILE) --env-file $(ENV_FILE) down

## Tail logs from Docker Compose (usage: make docker-logs service=backend)
docker-logs:
	$(COMPOSE) -f $(COMPOSE_FILE) --env-file $(ENV_FILE) logs -f $(service)

## List Docker Compose services status
docker-ps:
	$(COMPOSE) -f $(COMPOSE_FILE) --env-file $(ENV_FILE) ps

## Cleanup local cache directories
clean:
	rm -rf .pytest_cache .mypy_cache __pycache__

__ensure-env:
	@test -f $(ENV_FILE) || (echo "$(ENV_FILE) not found. Copy .env.example to $(ENV_FILE) first." && exit 1)
