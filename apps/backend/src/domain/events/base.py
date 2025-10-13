"""
Uzinex Boost — Domain Event Base
================================

Базовый класс и типы событий для доменного уровня системы Uzinex Boost.

Назначение:
- служит фундаментом для всех событий домена;
- обеспечивает единый формат данных, timestamp и идентификатор события;
- используется EventDispatcher'ом для публикации и логирования.

Паттерн: Domain Event (DDD)
---------------------------
Каждое событие описывает факт, который уже произошёл в системе.
Сервисы создают события, а адаптеры и обработчики на них реагируют.

Пример:
--------
event = BalanceUpdatedEvent(user_id=42, amount=+50.0, ...)
await EventDispatcher.publish(event)
"""

from __future__ import annotations
import uuid
from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


# -------------------------------------------------
# 🔹 Базовый доменный ивент
# -------------------------------------------------
class DomainEvent(BaseModel):
    """
    Базовый класс для всех событий домена Uzinex Boost.
    """

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Уникальный идентификатор события")
    event_type: str = Field(..., description="Тип события (например: balance.updated, user.registered)")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Время генерации события (UTC)")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Дополнительные метаданные события")

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {datetime: lambda v: v.isoformat()}
        orm_mode = True

    # -------------------------------------------------
    # 🔹 Утилиты
    # -------------------------------------------------
    def to_dict(self) -> Dict[str, Any]:
        """Преобразует событие в словарь для логирования или публикации."""
        return self.model_dump()

    def to_json(self) -> str:
        """Возвращает JSON-представление события."""
        return self.model_dump_json(indent=2)

    def __str__(self) -> str:
        return f"<DomainEvent {self.event_type} id={self.id} at={self.timestamp.isoformat()}>"

    # -------------------------------------------------
    # 🔹 Фабричный метод
    # -------------------------------------------------
    @classmethod
    def from_payload(cls, payload: Dict[str, Any]) -> "DomainEvent":
        """
        Создаёт событие из словаря данных (например, из брокера сообщений).
        """
        return cls(**payload)
