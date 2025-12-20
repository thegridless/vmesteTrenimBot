"""
Pydantic схемы для мероприятий.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class EventBase(BaseModel):
    """Базовые поля мероприятия."""

    title: str
    description: str | None = None
    date: datetime
    location: str | None = None


class EventCreate(EventBase):
    """Схема для создания мероприятия."""

    creator_id: int
    latitude: float | None = None  # Геолокация
    longitude: float | None = None  # Геолокация
    sport_type: str | None = None  # Вид спорта
    max_participants: int | None = None  # Количество человек
    fee: float | None = None  # Взносы
    note: str | None = None  # Примечание создателя


class EventUpdate(BaseModel):
    """Схема для обновления мероприятия (все поля опциональны)."""

    title: str | None = None
    description: str | None = None
    date: datetime | None = None
    location: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    sport_type: str | None = None
    max_participants: int | None = None
    fee: float | None = None
    note: str | None = None


class EventResponse(EventBase):
    """Схема ответа с данными мероприятия."""

    id: int
    creator_id: int
    latitude: float | None = None
    longitude: float | None = None
    sport_type: str | None = None
    max_participants: int | None = None
    fee: float | None = None
    note: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EventWithParticipants(EventResponse):
    """Мероприятие с количеством участников."""

    participants_count: int = 0


class ParticipantBase(BaseModel):
    """Базовые поля участника."""

    user_id: int
    event_id: int


class ParticipantCreate(ParticipantBase):
    """Схема для добавления участника."""

    pass


class ParticipantResponse(ParticipantBase):
    """Схема ответа с данными участника."""

    id: int
    joined_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PaginatedResponse(BaseModel):
    """Базовая схема для пагинированных ответов."""

    total: int
    page: int
    per_page: int
    pages: int


# --- Заявки на участие ---


class EventApplicationBase(BaseModel):
    """Базовые поля заявки на участие."""

    user_id: int
    event_id: int


class EventApplicationCreate(EventApplicationBase):
    """Схема для создания заявки на участие."""

    pass


class EventApplicationResponse(EventApplicationBase):
    """Схема ответа с данными заявки."""

    id: int
    status: str  # pending, approved, rejected
    applied_at: datetime
    reviewed_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class EventApplicationUpdate(BaseModel):
    """Схема для обновления статуса заявки."""

    status: str  # approved, rejected


class EventSearchParams(BaseModel):
    """Параметры поиска событий."""

    sport_type: str | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None
    skip: int = 0
    limit: int = 100
