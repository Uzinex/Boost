"""Handlers responsible for payment-related interactions."""

from __future__ import annotations

import logging
from typing import Any

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove

from ..service.api import APIClientError, BoostAPIClient


logger = logging.getLogger("boost.bot.handlers.payments")

router = Router(name="payments")


class ManualDepositState(StatesGroup):
    """Conversation states for manual deposit request."""

    waiting_for_amount = State()
    waiting_for_receipt = State()


def _get_api_client(message: Message | CallbackQuery) -> BoostAPIClient:
    api_client = message.bot.get("api_client") if isinstance(message, Message) else message.message.bot.get("api_client")
    if not isinstance(api_client, BoostAPIClient):
        raise RuntimeError("BoostAPIClient is not configured")
    return api_client


@router.callback_query(F.data == "payments:deposit")
async def cb_deposit(callback: CallbackQuery, state: FSMContext) -> None:
    """Initiate manual deposit request flow."""

    await callback.answer()
    await state.set_state(ManualDepositState.waiting_for_amount)
    await callback.message.answer(
        "💳 Введите сумму пополнения в UZT (например, 150 или 200.5).\n"
        "Если передумали — отправьте /cancel."
    )


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext) -> None:
    """Allow user to cancel the current payment flow."""

    if await state.get_state() is None:
        return

    await state.clear()
    await message.answer("Операция отменена.", reply_markup=ReplyKeyboardRemove())


@router.message(ManualDepositState.waiting_for_amount)
async def process_amount(message: Message, state: FSMContext) -> None:
    """Validate and store the deposit amount."""

    raw_amount = (message.text or "").replace(",", ".").strip()
    try:
        amount = float(raw_amount)
    except ValueError:
        await message.answer("Пожалуйста, отправьте сумму числом. Пример: <b>150</b> или <b>250.5</b>.")
        return

    if amount <= 0:
        await message.answer("Сумма должна быть положительной.")
        return

    await state.update_data(amount=amount)
    await state.set_state(ManualDepositState.waiting_for_receipt)
    await message.answer(
        "📸 Теперь отправьте фото или скан чека. Оно должно быть отправлено как изображение,"
        " не файлом. Если хотите отменить — используйте /cancel.",
        reply_markup=ReplyKeyboardRemove(),
    )


@router.message(ManualDepositState.waiting_for_receipt)
async def process_receipt(message: Message, state: FSMContext) -> None:
    """Finalize manual deposit request by sending data to backend."""

    if not message.photo:
        await message.answer("Нужно отправить фото чека. Попробуйте ещё раз.")
        return

    user = message.from_user
    if not user:
        await message.answer("Не удалось определить пользователя. Попробуйте позже.")
        await state.clear()
        return

    data: dict[str, Any] = await state.get_data()
    amount = data.get("amount")
    if amount is None:
        await message.answer("Не найдена сумма пополнения. Начните заново командой /start.")
        await state.clear()
        return

    receipt_file_id = message.photo[-1].file_id
    api_client = _get_api_client(message)

    try:
        response = await api_client.submit_manual_deposit(
            telegram_id=user.id,
            amount=float(amount),
            receipt_file_id=receipt_file_id,
        )
    except APIClientError as exc:
        logger.error("Failed to submit manual deposit: %s", exc)
        await message.answer(
            "⚠️ Не удалось отправить заявку на пополнение. Попробуйте позднее или обратитесь в поддержку.",
            reply_markup=ReplyKeyboardRemove(),
        )
    else:
        invoice_id = response.get("invoice_id")
        status = response.get("status", "pending")
        await message.answer(
            (
                "✅ Заявка отправлена!\n"
                f"ID заявки: <b>{invoice_id or '—'}</b>\n"
                f"Статус: <b>{status}</b>\n\n"
                "Мы уведомим вас после проверки администратора."
            ),
            reply_markup=ReplyKeyboardRemove(),
        )
    finally:
        await state.clear()


@router.callback_query(F.data == "payments:rates")
async def cb_rates(callback: CallbackQuery) -> None:
    """Provide current exchange rates."""

    await callback.answer()
    api_client = _get_api_client(callback)
    try:
        rates = await api_client.fetch_exchange_rates()
    except APIClientError as exc:
        logger.error("Failed to fetch exchange rates: %s", exc)
        await callback.message.answer("Сейчас не можем получить тарифы. Попробуйте позже.")
        return

    uzs_rate = rates.get("UZT_to_SUM")
    min_deposit = rates.get("min_deposit")
    parts = ["💱 <b>Текущие тарифы</b>"]
    if uzs_rate:
        parts.append(f"1 UZT ≈ <b>{uzs_rate}</b> сум")
    if min_deposit:
        parts.append(f"Минимальная сумма пополнения: <b>{min_deposit} UZT</b>")

    await callback.message.answer("\n".join(parts))
