"""
Pydantic схемы для видов спорта.
"""

from pydantic import BaseModel, Field


class SportBase(BaseModel):
    """Базовая схема вида спорта."""

    name: str = Field(..., min_length=2, max_length=100, description="Название вида спорта")
    active: bool = Field(default=True, description="Активен ли вид спорта")


class SportCreate(SportBase):
    """Схема создания вида спорта."""

    pass


class SportUpdate(BaseModel):
    """Схема обновления вида спорта."""

    name: str | None = Field(None, min_length=2, max_length=100)
    active: bool | None = None


class Sport(SportBase):
    """Схема вида спорта с ID."""

    id: int

    class Config:
        from_attributes = True
