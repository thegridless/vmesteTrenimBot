"""
SQLAlchemy модель рассылки.
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base

if TYPE_CHECKING:
    from src.users.models import User


class Broadcast(Base):
    """
    Модель рассылки сообщений.

    Attributes:
        id: Первичный ключ
        admin_user_id: ID администратора (FK на users)
        text: Текст рассылки
        status: Статус рассылки (pending/completed)
        total_count: Всего получателей
        success_count: Успешных отправок
        fail_count: Ошибок отправки
        created_at: Дата создания
        completed_at: Дата завершения
    """

    __tablename__ = "broadcasts"

    id: Mapped[int] = mapped_column(primary_key=True)
    admin_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    total_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    success_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    fail_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    admin_user: Mapped["User"] = relationship("User", lazy="selectin")

    def __str__(self) -> str:
        return (
            f"<Broadcast(id={self.id}, admin_user_id={self.admin_user_id}, status={self.status})>"
        )

    def __repr__(self) -> str:
        return self.__str__()
