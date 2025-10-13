"""Middlewares used by the Boost Telegram bot."""

from .dependency import DependencyInjectionMiddleware
from .logging import LoggingMiddleware

__all__ = ["DependencyInjectionMiddleware", "LoggingMiddleware"]
