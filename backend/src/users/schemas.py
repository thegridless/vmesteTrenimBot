"""
Pydantic схемы для пользователей.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class UserBase(BaseModel):
    """Базовые поля пользователя."""

    telegram_id: int
    username: str | None = None
    first_name: str


class UserCreate(UserBase):
    """Схема для создания пользователя (регистрация)."""

    age: int | None = None
    gender: str | None = None  # male, female, other
    city: str | None = None
    sports: list[str] | None = None  # Список видов спорта


class UserUpdate(BaseModel):
    """Схема для обновления пользователя (все поля опциональны)."""

    username: str | None = None
    first_name: str | None = None
    age: int | None = None
    gender: str | None = None
    city: str | None = None
    sports: list[str] | None = None
    note: str | None = None
    avatar_url: str | None = None


class UserResponse(UserBase):
    """Схема ответа с данными пользователя."""

    id: int
    age: int | None = None
    gender: str | None = None
    city: str | None = None
    sports: list[str] | None = None
    note: str | None = None
    avatar_url: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserWithEvents(UserResponse):
    """Пользователь с информацией о созданных и посещаемых мероприятиях."""

    created_events_count: int = 0
    participations_count: int = 0
