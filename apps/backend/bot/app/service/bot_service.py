"""High level orchestration layer for Telegram bot specific workflows."""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from typing import Any, Mapping, Sequence
from urllib.parse import unquote_plus

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.telegram import TelegramClient, send_notification as telegram_send_notification
from adapters.telegram.exceptions import TelegramMessageError
from adapters.telegram.notifier import broadcast as telegram_broadcast
from core.config import settings
from core.security import (
    build_user_payload,
    create_session_token,
    validate_telegram_init_data,
)
from db.models.user_model import User
from db.repositories.user_repository import UserRepository
from domain.services.payment_service import PaymentService

from .contracts import (
    ManualDepositResult,
    NotificationResult,
    TelegramUserSnapshot,
    WebAppAuthResult,
)
from .exceptions import BotServiceError, NotificationDeliveryError, WebAppAuthError

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import KeyboardButton, Message, ReplyKeyboardMarkup, WebAppInfo

router = Router()


def _build_main_keyboard() -> ReplyKeyboardMarkup:
    webapp_url = os.getenv("WEBAPP_URL") or settings.FRONTEND_URL or settings.BASE_DOMAIN
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text="🚀 Open WebApp",
                    web_app=WebAppInfo(url=webapp_url),
                )
            ]
        ],
        resize_keyboard=True,
        input_field_placeholder="Нажмите кнопку ниже 👇",
    )


@router.message(CommandStart())
async def start_cmd(message: Message) -> None:
    keyboard = _build_main_keyboard()
    await message.answer(
        "👋 Привет! Это <b>Uzinex Boost</b> 🚀\n\n"
        "💼 Через меня ты можешь выполнять задания и управлять балансом.\n\n"
        "Нажми кнопку ниже, чтобы открыть WebApp 👇",
        reply_markup=keyboard,
    )

@dataclass(slots=True)
class BotService:
    """Encapsulates business logic used by the Telegram bot integration."""

    session: AsyncSession
    telegram_client: TelegramClient
    logger: logging.Logger = logging.getLogger("uzinex.bot.service")

    def __post_init__(self) -> None:
        self.user_repository = UserRepository(self.session)

    # ------------------------------------------------------------------
    # 🔐  WebApp authorisation
    # ------------------------------------------------------------------
    async def authenticate_webapp(self, init_data: str, bot_token: str) -> WebAppAuthResult:
        """Validate Telegram ``initData`` and ensure the user exists."""

        if not init_data:
            raise WebAppAuthError("init_data is required")

        try:
            raw_payload = validate_telegram_init_data(init_data, bot_token)
        except HTTPException as exc:  # pragma: no cover - FastAPI specific exception
            raise WebAppAuthError(exc.detail) from exc

        user_payload = self._parse_user_payload(raw_payload)
        user = await self.user_repository.upsert_from_telegram(
            telegram_id=user_payload["id"],
            username=user_payload.get("username"),
            first_name=user_payload.get("first_name"),
            last_name=user_payload.get("last_name"),
            language_code=user_payload.get("language_code"),
        )

        token_payload = build_user_payload(user.id, user.username)
        session_token = create_session_token(token_payload)
        snapshot = self._build_snapshot(user)

        self.logger.info(
            "[BotService] WebApp auth for telegram_id=%s (user_id=%s)",
            user.telegram_id,
            user.id,
        )

        return WebAppAuthResult(
            session_token=session_token,
            user=snapshot,
            raw_payload=raw_payload,
        )

    async def create_debug_session(
        self,
        *,
        telegram_id: int | None = None,
        username: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
        language_code: str | None = None,
    ) -> WebAppAuthResult:
        """Создаёт сессию WebApp без ``initData`` (используется только в debug-режиме)."""

        if not settings.TELEGRAM_DEBUG_MODE:
            raise WebAppAuthError("Debug WebApp auth is disabled")

        resolved_telegram_id = telegram_id or settings.TELEGRAM_DEBUG_DEFAULT_USER_ID
        if not resolved_telegram_id:
            raise WebAppAuthError("telegram_id is required for debug session")

        resolved_username = username or settings.TELEGRAM_DEBUG_DEFAULT_USERNAME
        resolved_first_name = first_name or settings.TELEGRAM_DEBUG_DEFAULT_FIRST_NAME
        resolved_last_name = last_name or settings.TELEGRAM_DEBUG_DEFAULT_LAST_NAME
        resolved_language = language_code or settings.TELEGRAM_DEBUG_DEFAULT_LANGUAGE

        user = await self.user_repository.upsert_from_telegram(
            resolved_telegram_id,
            username=resolved_username,
            first_name=resolved_first_name,
            last_name=resolved_last_name,
            language_code=resolved_language,
        )

        token_payload = build_user_payload(user.id, user.username)
        session_token = create_session_token(token_payload)
        snapshot = self._build_snapshot(user)

        self.logger.info(
            "[BotService] Debug WebApp auth for telegram_id=%s (user_id=%s)",
            snapshot.telegram_id,
            snapshot.id,
        )

        raw_payload = {
            "mode": "debug",
            "user": {
                "id": snapshot.telegram_id,
                "username": snapshot.username,
                "first_name": snapshot.first_name,
                "last_name": snapshot.last_name,
                "language_code": snapshot.language_code,
            },
        }

        return WebAppAuthResult(
            session_token=session_token,
            user=snapshot,
            raw_payload=raw_payload,
        )

    # ------------------------------------------------------------------
    # 🔔  Notifications
    # ------------------------------------------------------------------
    async def notify_user(
        self,
        *,
        user_id: int | str,
        text: str,
        message_type: str = "info",
        photo_url: str | None = None,
        reply_markup: Mapping[str, Any] | None = None,
        parse_mode: str = "HTML",
    ) -> NotificationResult:
        """Send a notification to a Telegram user via the configured client."""

        if not text.strip():
            raise NotificationDeliveryError("Notification text cannot be empty")

        try:
            delivered = await telegram_send_notification(
                self.telegram_client,
                user_id,
                text,
                message_type=message_type,
                photo_url=photo_url,
                parse_mode=parse_mode,
                reply_markup=reply_markup,
            )
        except TelegramMessageError as exc:
            self.logger.warning(
                "[BotService] Telegram delivery failed for %s: %s", user_id, exc
            )
            raise NotificationDeliveryError(str(exc)) from exc
        except Exception as exc:  # pragma: no cover - unexpected runtime issues
            self.logger.exception(
                "[BotService] Unexpected error while sending notification to %s", user_id
            )
            raise NotificationDeliveryError("Failed to deliver notification") from exc

        return NotificationResult(
            delivered=delivered,
            user_id=user_id,
            message_type=message_type,
            text=text,
        )

    async def broadcast(
        self,
        user_ids: Sequence[int | str],
        text: str,
        *,
        message_type: str = "info",
    ) -> int:
        """Broadcast a message to multiple Telegram users."""

        if not user_ids:
            return 0
        return await telegram_broadcast(
            self.telegram_client,
            list(user_ids),
            text,
            message_type=message_type,
        )

    # ------------------------------------------------------------------
    # 💰  Manual deposits & balances
    # ------------------------------------------------------------------
    async def submit_manual_deposit(
        self,
        telegram_id: int,
        amount: float,
        receipt_file_id: str,
    ) -> ManualDepositResult:
        """Create a manual deposit request for a Telegram user."""

        if amount <= 0:
            raise BotServiceError("Amount must be greater than zero")

        user = await self.user_repository.get_by_telegram_id(telegram_id)
        if not user:
            raise BotServiceError(f"User with telegram_id={telegram_id} not found")

        payment_service = PaymentService(self.session)
        response = await payment_service.create_payment(
            user_id=user.id,
            amount=amount,
            method="manual",
            direction="in",
            metadata={"receipt_file_id": receipt_file_id},
        )

        if not response.get("success", False):
            raise BotServiceError(response.get("message", "Failed to create manual deposit"))

        status = response.get("status", "pending")
        payment_id = response.get("payment_id")

        self.logger.info(
            "[BotService] Manual deposit created for user_id=%s amount=%.2f (payment_id=%s)",
            user.id,
            amount,
            payment_id,
        )

        return ManualDepositResult(ok=True, status=status, payment_id=payment_id)

    async def get_user_balance(self, telegram_id: int) -> float | None:
        """Return the user's balance in UZT, if the user exists."""

        user = await self.user_repository.get_by_telegram_id(telegram_id)
        if not user:
            return None
        return float(user.balance)

    async def get_user_snapshot(self, telegram_id: int) -> TelegramUserSnapshot | None:
        """Fetch a user snapshot by their Telegram identifier."""

        user = await self.user_repository.get_by_telegram_id(telegram_id)
        if not user:
            return None
        return self._build_snapshot(user)

    # ------------------------------------------------------------------
    # ⚙️  Internal helpers
    # ------------------------------------------------------------------
    def _parse_user_payload(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        """Parse and validate the user section of Telegram init data."""

        user_raw = payload.get("user")
        if not user_raw:
            raise WebAppAuthError("Telegram init data does not contain user payload")

        try:
            decoded = unquote_plus(str(user_raw))
            user_payload = json.loads(decoded)
        except (TypeError, json.JSONDecodeError) as exc:
            raise WebAppAuthError("Telegram user payload is not valid JSON") from exc

        if "id" not in user_payload:
            raise WebAppAuthError("Telegram user payload is missing the 'id' field")

        return user_payload

    def _build_snapshot(self, user: User) -> TelegramUserSnapshot:
        """Create a :class:`TelegramUserSnapshot` from a :class:`User` model."""

        return TelegramUserSnapshot(
            id=user.id,
            telegram_id=user.telegram_id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            language_code=user.language_code,
            balance=float(user.balance or 0.0),
            is_admin=bool(user.is_admin),
            is_banned=bool(user.is_banned),
        )


__all__ = ["BotService"]
