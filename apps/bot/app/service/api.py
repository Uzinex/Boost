"""HTTP client for interacting with the Boost backend."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, Mapping, MutableMapping

import httpx


logger = logging.getLogger("boost.bot.api")


class APIClientError(RuntimeError):
    """Raised when the backend returns a non-successful response."""

    def __init__(self, message: str, *, status_code: int | None = None, payload: Any | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.payload = payload


@dataclass(slots=True)
class BoostAPIClient:
    """A thin asynchronous HTTP client tailored for the Boost backend API."""

    base_url: str
    token: str | None = None
    timeout: float = 10.0

    def __post_init__(self) -> None:
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=httpx.Timeout(self.timeout),
            headers=self._default_headers,
        )

    @property
    def _default_headers(self) -> Dict[str, str]:
        headers: Dict[str, str] = {
            "User-Agent": "BoostBot/1.0",
            "Accept": "application/json",
        }
        if self.token:
            headers["X-Bot-Token"] = self.token
        return headers

    async def aclose(self) -> None:
        """Close underlying HTTP client."""
        await self._client.aclose()

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        json: Mapping[str, Any] | None = None,
        headers: MutableMapping[str, str] | None = None,
    ) -> Dict[str, Any]:
        request_headers = dict(self._default_headers)
        if headers:
            request_headers.update(headers)

        try:
            response = await self._client.request(method, path, params=params, json=json, headers=request_headers)
        except httpx.HTTPError as exc:
            raise APIClientError(f"Failed to call backend: {exc}") from exc

        if response.status_code >= 400:
            detail: Any
            try:
                detail = response.json()
            except ValueError:
                detail = response.text
            raise APIClientError(
                f"Backend responded with HTTP {response.status_code}",
                status_code=response.status_code,
                payload=detail,
            )

        if response.content:
            try:
                return response.json()
            except ValueError as exc:
                raise APIClientError("Backend returned invalid JSON response") from exc
        return {}

    async def fetch_public_stats(self) -> Dict[str, Any]:
        """Fetch public statistics available for all users."""
        payload = await self._request("GET", "/stats/public")
        return payload.get("data", {})

    async def fetch_exchange_rates(self) -> Dict[str, Any]:
        """Fetch the current exchange rates for UZT conversions."""
        payload = await self._request("GET", "/payments/rates")
        return payload.get("rates", {})

    async def fetch_system_stats(self) -> Dict[str, Any]:
        """Fetch extended system statistics (admin scope)."""
        payload = await self._request("GET", "/stats/system")
        return payload.get("data", payload)

    async def ping(self) -> Dict[str, Any]:
        """Call the `/system/ping` endpoint."""
        return await self._request("GET", "/system/ping")

    async def health(self) -> Dict[str, Any]:
        """Call the `/system/health` endpoint."""
        return await self._request("GET", "/system/health")

    async def send_notification(self, user_id: int, text: str) -> Dict[str, Any]:
        """Send a notification to a user through the backend telegram adapter."""
        params = {"user_id": user_id, "text": text}
        return await self._request("POST", "/telegram/notify", params=params)

    async def submit_manual_deposit(
        self,
        *,
        telegram_id: int,
        amount: float,
        receipt_file_id: str,
    ) -> Dict[str, Any]:
        """Submit a manual deposit request on behalf of a Telegram user."""
        params = {
            "amount": amount,
            "check_photo_url": receipt_file_id,
        }
        headers = {"X-Telegram-Id": str(telegram_id)}
        return await self._request("POST", "/payments/manual", params=params, headers=headers)

    async def fetch_balance(self, telegram_id: int) -> float | None:
        """Retrieve the current user balance."""
        headers = {"X-Telegram-Id": str(telegram_id)}
        payload = await self._request("GET", "/balance/", headers=headers)
        return float(payload.get("balance")) if "balance" in payload else None


__all__ = ["BoostAPIClient", "APIClientError"]
