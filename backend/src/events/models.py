"""
SQLAlchemy модели для мероприятий (тренировок).
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base

if TYPE_CHECKING:
    from src.sports.models import Sport
    from src.users.models import User


class Event(Base):
    """
    Модель мероприятия (тренировки).

    Attributes:
        id: Первичный ключ
        title: Название мероприятия
        description: Описание
        date: Дата и время проведения
        location: Место проведения (текст)
        latitude: Широта (геолокация)
        longitude: Долгота (геолокация)
        sport_id: ID вида спорта (FK на Sport)
        max_participants: Максимальное количество участников
        fee: Взнос (опционально)
        note: Примечание создателя
        creator_id: ID создателя (FK на User)
        created_at: Дата создания записи
    """

    __tablename__ = "events"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    location: Mapped[str | None] = mapped_column(String(500), nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)  # Геолокация
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)  # Геолокация
    sport_id: Mapped[int | None] = mapped_column(
        ForeignKey("sports.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )  # ID вида спорта
    max_participants: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )  # Количество человек
    fee: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)  # Взносы
    note: Mapped[str | None] = mapped_column(Text, nullable=True)  # Примечание создателя
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

    # Связь с видом спорта
    sport: Mapped["Sport | None"] = relationship(
        "Sport",
        back_populates="events",
        lazy="selectin",
    )

    # Связь с участниками (many-to-many через EventParticipant)
    participants: Mapped[list["EventParticipant"]] = relationship(
        "EventParticipant",
        back_populates="event",
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    # Связь с заявками на участие
    applications: Mapped[list["EventApplication"]] = relationship(
        "EventApplication",
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


class EventApplication(Base):
    """
    Модель заявки на участие в мероприятии.
    Создатель события должен подтвердить заявку перед добавлением участника.

    Attributes:
        id: Первичный ключ
        user_id: ID пользователя, подавшего заявку
        event_id: ID мероприятия
        status: Статус заявки (pending, approved, rejected)
        applied_at: Дата подачи заявки
        reviewed_at: Дата рассмотрения заявки
    """

    __tablename__ = "event_applications"

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
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
        index=True,
    )  # pending, approved, rejected
    applied_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Связи
    user: Mapped["User"] = relationship(
        "User",
        back_populates="event_applications",
        lazy="selectin",
    )
    event: Mapped["Event"] = relationship(
        "Event",
        back_populates="applications",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<EventApplication(user_id={self.user_id}, event_id={self.event_id}, status={self.status})>"
