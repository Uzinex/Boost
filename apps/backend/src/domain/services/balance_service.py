"""
Uzinex Boost — Balance Service
==============================

Сервис управления балансом пользователей (UZT).

Назначение:
-----------
Реализует финансовые операции:
- начисления и списания;
- переводы между пользователями;
- аналитика и история транзакций;
- контроль лимитов и безопасности.

Интеграция:
------------
• domain.rules.balance_rules      — политика и ограничения;
• domain.events.balance_events    — события операций;
• db.repositories.transaction_repository — хранение транзакций;
• db.repositories.user_repository       — обновление баланса пользователя.
"""

from __future__ import annotations
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from domain.services.base import BaseService
from domain.rules.balance_rules import BalanceRules
from domain.events.balance_events import (
    BalanceUpdatedEvent,
    BalanceWithdrawnEvent,
    BalanceDepositedEvent,
    BalanceTransferredEvent,
)
from db.repositories.transaction_repository import TransactionRepository
from db.repositories.user_repository import UserRepository


class BalanceService(BaseService):
    """
    Сервис для управления балансами пользователей (UZT).
    """

    def __init__(self, session: AsyncSession):
        super().__init__(session)
        self.tx_repo = TransactionRepository(session)
        self.user_repo = UserRepository(session)

    # -------------------------------------------------
    # 🔹 Получить баланс пользователя
    # -------------------------------------------------
    async def get_balance(self, user_id: int) -> Optional[float]:
        """
        Возвращает текущий баланс пользователя.
        """
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            return None
        return float(user.balance)

    # -------------------------------------------------
    # 🔹 Пополнение баланса
    # -------------------------------------------------
    async def deposit(self, user_id: int, amount: float, payment_id: Optional[int] = None):
        """
        Пополняет баланс пользователя после успешного платежа.
        """
        # Проверка правил
        result = await BalanceRules.can_deposit(amount)
        if not result.is_allowed:
            return {"success": False, "message": result.message}

        user = await self.user_repo.get_by_id(user_id)
        if not user:
            return {"success": False, "message": "Пользователь не найден"}

        user.balance += amount

        # Создаём запись о транзакции
        tx = await self.tx_repo.create_transaction(
            user_id=user_id,
            amount=amount,
            tx_type="deposit",
            description="Пополнение баланса",
            payment_id=payment_id,
        )
        await self.publish_event(
            BalanceDepositedEvent(user_id=user_id, amount=amount, transaction_id=tx.id)
        )

        await self.commit()
        await self.log(f"Баланс пополнен: {user_id} (+{amount} UZT)")
        return {"success": True, "balance": user.balance, "transaction_id": tx.id}

    # -------------------------------------------------
    # 🔹 Снятие средств (вывод)
    # -------------------------------------------------
    async def withdraw(self, user_id: int, amount: float):
        """
        Списывает средства с баланса пользователя (вывод).
        """
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            return {"success": False, "message": "Пользователь не найден"}

        # Проверка лимитов и ограничений
        rule_result = await BalanceRules.can_withdraw(user_id, amount, self.tx_repo)
        if not rule_result.is_allowed:
            return {"success": False, "message": rule_result.message}

        if user.balance < amount:
            return {"success": False, "message": "Недостаточно средств на балансе"}

        user.balance -= amount

        tx = await self.tx_repo.create_transaction(
            user_id=user_id,
            amount=-amount,
            tx_type="withdraw",
            description="Вывод средств",
        )

        await self.publish_event(
            BalanceWithdrawnEvent(user_id=user_id, amount=amount, transaction_id=tx.id)
        )
        await self.commit()
        await self.log(f"Вывод средств: {user_id} (-{amount} UZT)")
        return {"success": True, "balance": user.balance, "transaction_id": tx.id}

    # -------------------------------------------------
    # 🔹 Перевод между пользователями
    # -------------------------------------------------
    async def transfer(self, sender_id: int, receiver_id: int, amount: float):
        """
        Переводит средства между пользователями.
        """
        # Проверка правил
        rule_result = await BalanceRules.can_transfer(sender_id, receiver_id, amount)
        if not rule_result.is_allowed:
            return {"success": False, "message": rule_result.message}

        sender = await self.user_repo.get_by_id(sender_id)
        receiver = await self.user_repo.get_by_id(receiver_id)
        if not sender or not receiver:
            return {"success": False, "message": "Пользователь не найден"}

        if sender.balance < amount:
            return {"success": False, "message": "Недостаточно средств для перевода"}

        sender.balance -= amount
        receiver.balance += amount

        # Две записи о транзакциях
        tx_sender = await self.tx_repo.create_transaction(
            user_id=sender_id,
            amount=-amount,
            tx_type="transfer_out",
            description=f"Перевод пользователю {receiver_id}",
        )
        tx_receiver = await self.tx_repo.create_transaction(
            user_id=receiver_id,
            amount=amount,
            tx_type="transfer_in",
            description=f"Перевод от пользователя {sender_id}",
        )

        await self.publish_event(
            BalanceTransferredEvent(
                sender_id=sender_id,
                receiver_id=receiver_id,
                amount=amount,
                sender_tx_id=tx_sender.id,
                receiver_tx_id=tx_receiver.id,
            )
        )

        await self.commit()
        await self.log(f"Перевод: {sender_id} → {receiver_id} ({amount} UZT)")
        return {"success": True, "amount": amount, "sender_balance": sender.balance}

    # -------------------------------------------------
    # 🔹 История транзакций
    # -------------------------------------------------
    async def get_transaction_history(self, user_id: int, limit: int = 50):
        """
        Возвращает последние транзакции пользователя.
        """
        transactions = await self.tx_repo.get_by_user(user_id=user_id, limit=limit)
        return [tx.as_dict() for tx in transactions]

    # -------------------------------------------------
    # 🔹 Актуальный баланс и статистика
    # -------------------------------------------------
    async def get_balance_summary(self, user_id: int):
        """
        Возвращает агрегированные данные по операциям пользователя.
        """
        summary = await self.tx_repo.get_summary_by_user(user_id)
        current_balance = await self.get_balance(user_id)
        summary["current_balance"] = current_balance
        await self.log(f"Получен отчёт по балансу пользователя: {user_id}")
        return summary

    # -------------------------------------------------
    # 🔹 Принудительное обновление баланса (админ)
    # -------------------------------------------------
    async def adjust_balance(self, user_id: int, amount: float, reason: str):
        """
        Принудительно корректирует баланс (используется администратором).
        """
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            return {"success": False, "message": "Пользователь не найден"}

        user.balance += amount
        tx = await self.tx_repo.create_transaction(
            user_id=user_id,
            amount=amount,
            tx_type="adjustment",
            description=reason,
        )

        await self.publish_event(
            BalanceUpdatedEvent(user_id=user_id, amount=amount, reason=reason, transaction_id=tx.id)
        )
        await self.commit()
        await self.log(f"Корректировка баланса пользователя {user_id}: {amount} UZT ({reason})")
        return {"success": True, "balance": user.balance}
