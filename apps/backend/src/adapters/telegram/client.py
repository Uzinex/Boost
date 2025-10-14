"""
Uzinex Boost — Telegram Client Adapter
======================================

Асинхронный клиент для взаимодействия с Telegram Bot API.

Назначение:
- отправка сообщений пользователям и администраторам;
- безопасное выполнение запросов к Bot API;
- логирование, контроль ошибок и таймаутов.

Используется backend-сервисами (например, PaymentService, BoostNotifier)
для коммуникации с пользователями через Telegram.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

import httpx
from .exceptions import TelegramAPIError

logger = logging.getLogger("uzinex.telegram.client")


class TelegramClient:
    """
    Лёгкий асинхронный клиент для Telegram Bot API.
    Подходит для серверного использования без aiogram.
    """

    def __init__(
        self,
        token: str,
        api_url: str = "https://api.telegram.org",
        timeout: float = 10.0,
        retry_attempts: int = 2,
    ):
        self.token = token.strip()
        self.api_url = api_url.rstrip("/")
        self.timeout = timeout
        self.retry_attempts = retry_attempts
        self._client = httpx.AsyncClient(timeout=self.timeout)

    # -------------------------------------------------
    # 🔹 Внутренние методы
    # -------------------------------------------------

    @property
    def base_url(self) -> str:
        """Полный URL до Bot API."""
        return f"{self.api_url}/bot{self.token}"

    async def _request(self, method: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Выполняет HTTP-запрос к Telegram Bot API с логированием и retry.
        """
        url = f"{self.base_url}/{method}"
        payload = payload or {}

        for attempt in range(1, self.retry_attempts + 1):
            try:
                response = await self._client.post(url, data=payload)
                response.raise_for_status()
                data = response.json()
                if not data.get("ok"):
                    desc = data.get("description", "Unknown Telegram error")
                    raise TelegramAPIError(desc)
                return data
            except Exception as e:
                logger.warning(f"[Attempt {attempt}] Telegram API call failed: {e}")
                if attempt == self.retry_attempts:
                    logger.error(f"Telegram API request failed after {attempt} attempts.")
                    raise
        return {}

    # -------------------------------------------------
    # 🔹 Публичные методы API
    # -------------------------------------------------

    async def get_me(self) -> dict:
        """
        Получает информацию о текущем Telegram-боте.
        Аналог API-метода getMe.
        """
        try:
            data = await self._request("getMe")
            return data.get("result", {})
        except Exception as e:
            raise RuntimeError(f"Telegram getMe failed: {e}")

    async def send_message(
        self,
        chat_id: int | str,
        text: str,
        parse_mode: str = "HTML",
        disable_web_page_preview: bool = True,
        reply_markup: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Отправляет сообщение пользователю."""
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": disable_web_page_preview,
        }
        if reply_markup:
            payload["reply_markup"] = reply_markup

        logger.info(f"[Telegram] → {chat_id}: {text[:100]}")
        return await self._request("sendMessage", payload)

    async def send_photo(
        self,
        chat_id: int | str,
        photo_url: str,
        caption: Optional[str] = None,
        parse_mode: str = "HTML",
    ) -> Dict[str, Any]:
        """Отправляет изображение по URL."""
        payload = {"chat_id": chat_id, "photo": photo_url, "parse_mode": parse_mode}
        if caption:
            payload["caption"] = caption
        return await self._request("sendPhoto", payload)

    async def send_document(
        self,
        chat_id: int | str,
        file_url: str,
        caption: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Отправляет документ по URL."""
        payload = {"chat_id": chat_id, "document": file_url}
        if caption:
            payload["caption"] = caption
        return await self._request("sendDocument", payload)

    async def edit_message_text(
        self,
        chat_id: int | str,
        message_id: int,
        new_text: str,
        parse_mode: str = "HTML",
    ) -> Dict[str, Any]:
        """Редактирует ранее отправленное сообщение."""
        payload = {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": new_text,
            "parse_mode": parse_mode,
        }
        return await self._request("editMessageText", payload)

    async def answer_callback_query(
        self,
        callback_query_id: str,
        text: str,
        show_alert: bool = False,
    ) -> None:
        """Отвечает на callback-запрос (для WebApp inline-кнопок)."""
        payload = {
            "callback_query_id": callback_query_id,
            "text": text,
            "show_alert": show_alert,
        }
        await self._request("answerCallbackQuery", payload)

    # -------------------------------------------------
    # 🔹 Завершение
    # -------------------------------------------------

    async def close(self) -> None:
        """Закрывает HTTP-клиент."""
        await self._client.aclose()
        logger.info("🔒 TelegramClient session closed.")
