"""
Модели для видов спорта.
"""

from database import Base
from sqlalchemy import Boolean, Column, Integer, String
from sqlalchemy.orm import relationship


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

    def __repr__(self):
        return f"<Sport(id={self.id}, name='{self.name}', active={self.active})>"
