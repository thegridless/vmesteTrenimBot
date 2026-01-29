"""
API роутер для работы с весами пользователей.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_session
from src.users.repository import UserRepository
from src.weights.repository import WeightRepository
from src.weights.schemas import WeightCreate, WeightProgressItem, WeightResponse

router = APIRouter(prefix="/weights", tags=["weights"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


def get_weight_repository(session: SessionDep) -> WeightRepository:
    """
    Dependency для получения репозитория весов.

    Args:
        session: Асинхронная сессия БД

    Returns:
        Экземпляр WeightRepository
    """
    return WeightRepository(session)


def get_user_repository(session: SessionDep) -> UserRepository:
    """
    Dependency для получения репозитория пользователей.

    Args:
        session: Асинхронная сессия БД

    Returns:
        Экземпляр UserRepository
    """
    return UserRepository(session)


WeightRepoDep = Annotated[WeightRepository, Depends(get_weight_repository)]
UserRepoDep = Annotated[UserRepository, Depends(get_user_repository)]


@router.post("/", response_model=WeightResponse, status_code=status.HTTP_201_CREATED)
async def create_weight(
    weight_data: WeightCreate,
    repo: WeightRepoDep,
    user_repo: UserRepoDep,
):
    """Создать запись веса."""
    user = await user_repo.get_by_id(weight_data.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден",
        )
    return await repo.create_weight(weight_data)


@router.get("/exercises", response_model=list[str])
async def get_user_exercises(
    user_id: int,
    repo: WeightRepoDep,
    user_repo: UserRepoDep,
):
    """Получить список уникальных упражнений пользователя."""
    user = await user_repo.get_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден",
        )
    return await repo.list_user_exercises(user_id)


@router.get("/progress", response_model=list[WeightProgressItem])
async def get_weight_progress(
    user_id: int,
    exercise: str,
    repo: WeightRepoDep,
    user_repo: UserRepoDep,
    limit: int = 5,
):
    """Получить прогресс по упражнению."""
    user = await user_repo.get_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден",
        )
    items = await repo.list_progress(user_id, exercise, limit=limit)
    return [WeightProgressItem(date=item.date, weight=float(item.weight)) for item in items]
