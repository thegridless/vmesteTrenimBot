"""
SQLAlchemy модель пользовательских весов по упражнениям.
"""

from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Date, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base

if TYPE_CHECKING:
    from src.users.models import User


class Weight(Base):
    """
    Модель веса пользователя по упражнению.

    Attributes:
        id: Первичный ключ
        user_id: ID пользователя (FK на User)
        exercise: Название упражнения
        date: Дата замера
        weight: Вес (кг)
    """

    __tablename__ = "weights"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    exercise: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    weight: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)

    user: Mapped["User"] = relationship(
        "User",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Weight(user_id={self.user_id}, exercise={self.exercise}, date={self.date})>"
