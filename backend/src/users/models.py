"""
SQLAlchemy модель пользователя.
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, Integer, String, Table, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base

if TYPE_CHECKING:
    from src.events.models import Event, EventApplication, EventParticipant
    from src.sports.models import Sport


# Промежуточная таблица для связи many-to-many между User и Sport
user_sports = Table(
    "user_sports",
    Base.metadata,
    Column("user_id", ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("sport_id", ForeignKey("sports.id", ondelete="CASCADE"), primary_key=True),
)


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
        sports: Список видов спорта (many-to-many связь со Sport)
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

    # Связь с видами спорта (many-to-many)
    sports: Mapped[list["Sport"]] = relationship(
        "Sport",
        secondary=user_sports,
        back_populates="users",
        lazy="selectin",
    )

    def __str__(self) -> str:
        return f"<User(id={self.id}, telegram_id={self.telegram_id}, username={self.username})>"

    def __repr__(self) -> str:
        return self.__str__()
