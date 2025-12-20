"""
SQLAlchemy модели для мероприятий (тренировок).
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base

if TYPE_CHECKING:
    from src.users.models import User


class Event(Base):
    """
    Модель мероприятия (тренировки).

    Attributes:
        id: Первичный ключ
        title: Название мероприятия
        description: Описание
        date: Дата и время проведения
        location: Место проведения
        creator_id: ID создателя (FK на User)
        created_at: Дата создания записи
    """

    __tablename__ = "events"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    location: Mapped[str | None] = mapped_column(String(500), nullable=True)
    creator_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    # Связь с создателем
    creator: Mapped["User"] = relationship(
        "User",
        back_populates="created_events",
        lazy="selectin",
    )

    # Связь с участниками (many-to-many через EventParticipant)
    participants: Mapped[list["EventParticipant"]] = relationship(
        "EventParticipant",
        back_populates="event",
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Event(id={self.id}, title={self.title}, date={self.date})>"


class EventParticipant(Base):
    """
    Связующая таблица для many-to-many между User и Event.
    Хранит информацию об участии пользователя в мероприятии.

    Attributes:
        id: Первичный ключ
        user_id: ID пользователя
        event_id: ID мероприятия
        joined_at: Дата присоединения к мероприятию
    """

    __tablename__ = "event_participants"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    event_id: Mapped[int] = mapped_column(
        ForeignKey("events.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    # Связи
    user: Mapped["User"] = relationship(
        "User",
        back_populates="participations",
        lazy="selectin",
    )
    event: Mapped["Event"] = relationship(
        "Event",
        back_populates="participants",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<EventParticipant(user_id={self.user_id}, event_id={self.event_id})>"
