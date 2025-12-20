"""
SQLAlchemy модель пользователя.
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, BigInteger, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base

if TYPE_CHECKING:
    from src.events.models import Event, EventApplication, EventParticipant


class User(Base):
    """
    Модель пользователя Telegram.

    Attributes:
        id: Первичный ключ
        telegram_id: ID пользователя в Telegram (уникальный)
        username: Username в Telegram (опционально)
        first_name: Имя пользователя
        age: Возраст пользователя
        gender: Пол (male/female/other)
        city: Город
        sports: Список видов спорта (JSON массив)
        note: Примечание/описание пользователя
        avatar_url: URL аватарки
        created_at: Дата регистрации
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(
        BigInteger,
        unique=True,
        index=True,
        nullable=False,
    )
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    first_name: Mapped[str] = mapped_column(String(255), nullable=False)
    age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    gender: Mapped[str | None] = mapped_column(String(20), nullable=True)  # male, female, other
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    sports: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)  # Список видов спорта
    note: Mapped[str | None] = mapped_column(Text, nullable=True)  # Примечание пользователя
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)  # URL аватарки
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    # Связь с созданными мероприятиями
    created_events: Mapped[list["Event"]] = relationship(
        "Event",
        back_populates="creator",
        lazy="selectin",
    )

    # Связь с участием в мероприятиях (many-to-many)
    participations: Mapped[list["EventParticipant"]] = relationship(
        "EventParticipant",
        back_populates="user",
        lazy="selectin",
    )

    # Связь с заявками на участие
    event_applications: Mapped[list["EventApplication"]] = relationship(
        "EventApplication",
        back_populates="user",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, telegram_id={self.telegram_id}, username={self.username})>"
