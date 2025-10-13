"""
Uzinex Boost API v1 — Base Schemas
===================================

Базовые Pydantic-модели, используемые во всех схемах API.

Назначение:
- единый формат ответов (BaseResponse, ErrorResponse);
- стандартные поля идентификации и времени (IDMixin, TimestampMixin);
- совместимость с ORM-моделями (SQLAlchemy);
- унификация стиля API для Swagger / OpenAPI.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field


# -------------------------------------------------
# 🔹 Базовые миксины
# -------------------------------------------------

class IDMixin(BaseModel):
    """Добавляет стандартное поле ID в модель."""
    id: int = Field(..., description="Уникальный идентификатор объекта")

    class Config:
        orm_mode = True
        from_attributes = True


class TimestampMixin(BaseModel):
    """Добавляет временные метки создания и обновления."""
    created_at: datetime = Field(..., description="Дата и время создания")
    updated_at: Optional[datetime] = Field(None, description="Дата последнего обновления")

    class Config:
        orm_mode = True
        from_attributes = True


# -------------------------------------------------
# 🔹 Универсальные ответы API
# -------------------------------------------------

class BaseResponse(BaseModel):
    """Стандартный успешный ответ API."""
    ok: bool = Field(True, description="Статус успешности запроса")
    data: Optional[Any] = Field(None, description="Полезная нагрузка ответа")

    class Config:
        json_schema_extra = {
            "example": {
                "ok": True,
                "data": {"message": "Operation successful"}
            }
        }


class ErrorResponse(BaseModel):
    """Стандартный ответ при ошибке API."""
    ok: bool = Field(False, description="Флаг успешности (всегда False при ошибке)")
    detail: str = Field(..., description="Описание ошибки")
    code: Optional[int] = Field(None, description="Код ошибки (опционально)")

    class Config:
        json_schema_extra = {
            "example": {
                "ok": False,
                "detail": "Недостаточно средств для выполнения операции",
                "code": 400
            }
        }


# -------------------------------------------------
# 🔹 Универсальная пагинация
# -------------------------------------------------

class PaginatedResponse(BaseModel):
    """Базовая структура ответа с пагинацией."""
    ok: bool = Field(True, description="Статус запроса")
    total: int = Field(..., description="Общее количество элементов")
    page: int = Field(..., description="Номер текущей страницы (начиная с 1)")
    page_size: int = Field(..., description="Количество элементов на странице")
    items: list[Any] = Field(..., description="Список объектов текущей страницы")

    class Config:
        json_schema_extra = {
            "example": {
                "ok": True,
                "total": 100,
                "page": 1,
                "page_size": 20,
                "items": [{"id": 1, "name": "Example"}]
            }
        }
