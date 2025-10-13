"""High level orchestration layer for Telegram bot specific workflows."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any, Mapping, Sequence
from urllib.parse import unquote_plus

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from adapters.telegram import TelegramClient, send_notification as telegram_send_notification
from adapters.telegram.exceptions import TelegramMessageError
from adapters.telegram.notifier import broadcast as telegram_broadcast
from core.security import build_user_payload, create_session_token, validate_telegram_init_data
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
