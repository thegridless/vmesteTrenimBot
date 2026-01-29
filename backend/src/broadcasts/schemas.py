"""
Pydantic схемы для рассылок.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class BroadcastCreate(BaseModel):
    """Схема создания рассылки."""

    text: str = Field(..., min_length=1, max_length=4096, description="Текст рассылки")


class BroadcastComplete(BaseModel):
    """Схема завершения рассылки."""

    total_count: int = Field(..., ge=0, description="Всего получателей")
    success_count: int = Field(..., ge=0, description="Успешных отправок")
    fail_count: int = Field(..., ge=0, description="Ошибок отправки")


class BroadcastResponse(BaseModel):
    """Схема ответа с данными рассылки."""

    id: int
    admin_user_id: int
    text: str
    status: str
    total_count: int
    success_count: int
    fail_count: int
    created_at: datetime
    completed_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
