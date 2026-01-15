"""
Модели для видов спорта.
"""

from sqlalchemy import Boolean, Column, Integer, String
from sqlalchemy.orm import relationship

from src.database import Base


class Sport(Base):
    """
    Модель вида спорта.

    Attributes:
        id: ID вида спорта
        name: Название вида спорта
        active: Активен ли вид спорта
    """

    __tablename__ = "sports"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False, index=True)
    active = Column(Boolean, default=True, nullable=False)

    # Связи
    events = relationship("Event", back_populates="sport")
    users = relationship("User", secondary="user_sports", back_populates="sports")

    def __str__(self) -> str:
        return f"<Sport(id={self.id}, name='{self.name}', active={self.active})>"

    def __repr__(self) -> str:
        return self.__str__()
