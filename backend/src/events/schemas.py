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


class EventUpdate(BaseModel):
    """Схема для обновления мероприятия (все поля опциональны)."""

    title: str | None = None
    description: str | None = None
    date: datetime | None = None
    location: str | None = None


class EventResponse(EventBase):
    """Схема ответа с данными мероприятия."""

    id: int
    creator_id: int
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
