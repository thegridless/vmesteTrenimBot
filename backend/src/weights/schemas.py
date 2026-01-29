"""
Pydantic схемы для весов пользователя.
"""

from datetime import date as dt_date

from pydantic import BaseModel, ConfigDict, Field


class WeightBase(BaseModel):
    """Базовые поля записи веса."""

    user_id: int = Field(..., description="ID пользователя")
    exercise: str = Field(..., min_length=2, max_length=255, description="Название упражнения")
    date: dt_date = Field(..., description="Дата замера")
    weight: float = Field(..., gt=0, description="Вес (кг)")


class WeightCreate(WeightBase):
    """Схема создания записи веса."""

    pass


class WeightResponse(WeightBase):
    """Схема ответа с записью веса."""

    id: int

    model_config = ConfigDict(from_attributes=True)


class WeightProgressItem(BaseModel):
    """Позиция прогресса по упражнению."""

    date: dt_date = Field(..., description="Дата замера")
    weight: float = Field(..., description="Вес (кг)")
