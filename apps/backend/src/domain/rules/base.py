"""
Uzinex Boost — Domain Rules Base
================================

Базовые классы и структуры для системы бизнес-правил (Domain Rules Engine).

Назначение:
-----------
Определяет общий интерфейс для всех правил:
- декларативное описание условий;
- метод проверки (`evaluate`);
- унифицированный результат (`RuleResult`);
- поддержка асинхронного исполнения и логирования решений.

Паттерн: Specification / Policy / Rule Object
---------------------------------------------
Каждое правило определяет, разрешено ли выполнение действия,
и возвращает объект RuleResult с подробным описанием.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from loguru import logger


# -------------------------------------------------
# 🔹 Результат проверки правила
# -------------------------------------------------
class RuleResult(BaseModel):
    """
    Унифицированный результат проверки бизнес-правила.
    """

    is_allowed: bool = Field(..., description="Разрешено ли выполнение действия")
    message: str = Field("", description="Описание результата (например, причина отказа)")
    rule_name: str = Field("", description="Название правила")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Дополнительные данные")
    checked_at: datetime = Field(default_factory=datetime.utcnow)

    def __bool__(self) -> bool:
        return self.is_allowed

    def __str__(self) -> str:
        status = "✅ ALLOWED" if self.is_allowed else "❌ DENIED"
        return f"[{status}] {self.rule_name}: {self.message or 'OK'}"


# -------------------------------------------------
# 🔹 Базовый класс правила
# -------------------------------------------------
class BaseRule(ABC):
    """
    Абстрактный базовый класс для всех правил домена.
    Каждое правило должно реализовать метод `evaluate`.
    """

    rule_name: str = "UnnamedRule"

    @classmethod
    async def evaluate(cls, *args, **kwargs) -> RuleResult:
        """
        Выполняет асинхронную проверку условия.
        """
        try:
            allowed, message, meta = await cls._evaluate(*args, **kwargs)
            result = RuleResult(
                is_allowed=allowed,
                message=message or "",
                rule_name=cls.rule_name,
                metadata=meta or {},
            )
            logger.debug(f"[Rule] {result}")
            return result
        except Exception as e:
            logger.exception(f"[RuleError] {cls.rule_name}: {e}")
            return RuleResult(
                is_allowed=False,
                message=f"Ошибка при проверке правила: {str(e)}",
                rule_name=cls.rule_name,
            )

    @classmethod
    @abstractmethod
    async def _evaluate(cls, *args, **kwargs) -> tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """
        Реальная логика проверки (переопределяется в наследниках).
        Должна возвращать кортеж:
            (is_allowed: bool, message: str | None, metadata: dict | None)
        """
        ...


# -------------------------------------------------
# 🔹 Пример шаблона правила (для документации)
# -------------------------------------------------
class ExampleRule(BaseRule):
    """
    Пример использования базового правила.
    Проверяет, можно ли выполнить условное действие.
    """

    rule_name = "ExampleRule"

    @classmethod
    async def _evaluate(cls, value: int) -> tuple[bool, str, Dict[str, Any]]:
        if value > 10:
            return True, "Значение допустимо", {"value": value}
        return False, "Значение должно быть больше 10", {"value": value}
