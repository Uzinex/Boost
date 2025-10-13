"""
Uzinex Boost — Transaction Repository
=====================================

Репозиторий для работы с финансовыми транзакциями пользователей (UZT).

Назначение:
- регистрация всех операций с балансом;
- аналитика начислений и списаний;
- получение истории и статистики транзакций;
- интеграция с заданиями, заказами, платежами и рефералами.

Используется в:
- domain.services.balance
- api.v1.routes.balance
- adapters.payments
"""

from __future__ import annotations
from typing import List, Optional
from datetime import datetime

from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.balance_model import BalanceTransaction
from db.repositories.base import BaseRepository


class TransactionRepository(BaseRepository[BalanceTransaction]):
    """
    Репозиторий для управления всеми движениями UZT.
    """

    def __init__(self, session: AsyncSession):
        super().__init__(session, BalanceTransaction)

    # -------------------------------------------------
    # 🔹 Получить транзакции пользователя
    # -------------------------------------------------
    async def get_by_user(
        self,
        user_id: int,
        limit: int = 50,
        tx_type: Optional[str] = None,
    ) -> List[BalanceTransaction]:
        """
        Возвращает список транзакций пользователя (опционально по типу).
        """
        query = select(BalanceTransaction).where(BalanceTransaction.user_id == user_id)
        if tx_type:
            query = query.where(BalanceTransaction.type == tx_type)
        result = await self.session.execute(
            query.order_by(BalanceTransaction.created_at.desc()).limit(limit)
        )
        return result.scalars().all()

    # -------------------------------------------------
    # 🔹 Создать новую транзакцию
    # -------------------------------------------------
    async def create_transaction(
        self,
        user_id: int,
        amount: float,
        tx_type: str,
        description: str = "",
        order_id: Optional[int] = None,
        task_id: Optional[int] = None,
        payment_id: Optional[int] = None,
    ) -> BalanceTransaction:
        """
        Создаёт запись о транзакции: начисление, списание или бонус.
        """
        tx = BalanceTransaction(
            user_id=user_id,
            amount=amount,
            type=tx_type,
            description=description,
            order_id=order_id,
            task_id=task_id,
            payment_id=payment_id,
            created_at=datetime.utcnow(),
        )
        self.session.add(tx)
        await self.session.commit()
        await self.session.refresh(tx)
        return tx

    # -------------------------------------------------
    # 🔹 Агрегированная статистика по пользователю
    # -------------------------------------------------
    async def get_summary_by_user(self, user_id: int) -> dict:
        """
        Возвращает статистику по пользователю:
        - всего начислено,
        - всего списано,
        - итоговый чистый баланс.
        """
        result = await self.session.execute(
            select(
                func.sum(
                    func.case(
                        (BalanceTransaction.amount > 0, BalanceTransaction.amount),
                        else_=0,
                    )
                ).label("total_in"),
                func.sum(
                    func.case(
                        (BalanceTransaction.amount < 0, BalanceTransaction.amount),
                        else_=0,
                    )
                ).label("total_out"),
            ).where(BalanceTransaction.user_id == user_id)
        )
        total_in, total_out = result.one_or_none() or (0.0, 0.0)
        return {
            "total_in": round(float(total_in or 0), 2),
            "total_out": round(abs(float(total_out or 0)), 2),
            "net_balance": round(float((total_in or 0) + (total_out or 0)), 2),
        }

    # -------------------------------------------------
    # 🔹 Статистика по типам транзакций
    # -------------------------------------------------
    async def get_stats_by_type(self, user_id: Optional[int] = None) -> dict:
        """
        Возвращает статистику транзакций по типам:
        (earn, spend, referral, deposit, withdraw и т.д.)
        """
        query = select(
            BalanceTransaction.type,
            func.count(BalanceTransaction.id),
            func.sum(BalanceTransaction.amount),
        ).group_by(BalanceTransaction.type)

        if user_id:
            query = query.where(BalanceTransaction.user_id == user_id)

        result = await self.session.execute(query)
        return {
            tx_type: {
                "count": count,
                "sum": round(float(total or 0), 2),
            }
            for tx_type, count, total in result.all()
        }

    # -------------------------------------------------
    # 🔹 Последние транзакции
    # -------------------------------------------------
    async def get_recent(self, limit: int = 20) -> List[BalanceTransaction]:
        """
        Возвращает последние транзакции (для дашборда или админ-панели).
        """
        result = await self.session.execute(
            select(BalanceTransaction)
            .order_by(BalanceTransaction.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()

    # -------------------------------------------------
    # 🔹 Обновить описание транзакции
    # -------------------------------------------------
    async def update_description(self, tx_id: int, description: str) -> Optional[BalanceTransaction]:
        """
        Изменяет описание транзакции (например, добавить комментарий админа).
        """
        await self.session.execute(
            update(BalanceTransaction)
            .where(BalanceTransaction.id == tx_id)
            .values(description=description)
            .execution_options(synchronize_session="fetch")
        )
        await self.session.commit()
        return await self.get(tx_id)

    # -------------------------------------------------
    # 🔹 Глобальная статистика системы
    # -------------------------------------------------
    async def get_global_stats(self) -> dict:
        """
        Возвращает сводную статистику по всем транзакциям:
        - общее количество,
        - суммарный приток и отток средств,
        - чистый результат.
        """
        result = await self.session.execute(
            select(
                func.count(BalanceTransaction.id),
                func.sum(
                    func.case(
                        (BalanceTransaction.amount > 0, BalanceTransaction.amount),
                        else_=0,
                    )
                ),
                func.sum(
                    func.case(
                        (BalanceTransaction.amount < 0, BalanceTransaction.amount),
                        else_=0,
                    )
                ),
            )
        )
        count, total_in, total_out = result.one_or_none() or (0, 0.0, 0.0)
        return {
            "transactions": count,
            "total_in": round(float(total_in or 0), 2),
            "total_out": round(abs(float(total_out or 0)), 2),
            "net": round(float((total_in or 0) + (total_out or 0)), 2),
        }
