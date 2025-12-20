"""
SQLAlchemy модель пользователя.
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base

if TYPE_CHECKING:
    from src.events.models import Event, EventParticipant


class User(Base):
    """
    Модель пользователя Telegram.

    Attributes:
        id: Первичный ключ
        telegram_id: ID пользователя в Telegram (уникальный)
        username: Username в Telegram (опционально)
        first_name: Имя пользователя
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

    def __repr__(self) -> str:
        return f"<User(id={self.id}, telegram_id={self.telegram_id}, username={self.username})>"
