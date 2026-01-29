"""
API роутер для видов спорта.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_session
from src.sports.repository import SportRepository
from src.sports.schemas import Sport, SportCreate, SportUpdate

router = APIRouter(prefix="/sports", tags=["sports"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


def get_sport_repository(session: SessionDep) -> SportRepository:
    """
    Dependency для получения репозитория видов спорта.

    Args:
        session: Асинхронная сессия БД

    Returns:
        Экземпляр SportRepository
    """
    return SportRepository(session)


SportRepoDep = Annotated[SportRepository, Depends(get_sport_repository)]


@router.get("", response_model=list[Sport])
async def get_sports(
    repo: SportRepoDep,
    skip: int = 0,
    limit: int = 100,
    active_only: bool = False,
):
    """
    Получить список видов спорта.

    Args:
        repo: Репозиторий видов спорта
        skip: Сколько пропустить
        limit: Максимум записей
        active_only: Только активные виды спорта

    Returns:
        Список видов спорта
    """
    return await repo.list_sports(skip=skip, limit=limit, active_only=active_only)


@router.get("/{sport_id}", response_model=Sport)
async def get_sport(sport_id: int, repo: SportRepoDep):
    """
    Получить вид спорта по ID.

    Args:
        sport_id: ID вида спорта
        repo: Репозиторий видов спорта

    Returns:
        Вид спорта

    Raises:
        HTTPException: Если вид спорта не найден
    """
    sport = await repo.get_by_id(sport_id)
    if not sport:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Вид спорта не найден",
        )
    return sport


@router.post("", response_model=Sport, status_code=status.HTTP_201_CREATED)
async def create_sport(sport_data: SportCreate, repo: SportRepoDep):
    """
    Создать новый вид спорта.

    Args:
        sport_data: Данные для создания
        repo: Репозиторий видов спорта

    Returns:
        Созданный вид спорта

    Raises:
        HTTPException: Если вид спорта с таким названием уже существует
    """
    existing = await repo.get_by_name(sport_data.name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Вид спорта с таким названием уже существует",
        )
    return await repo.create_sport(sport_data)


@router.patch("/{sport_id}", response_model=Sport)
async def update_sport(
    sport_id: int,
    sport_update: SportUpdate,
    repo: SportRepoDep,
):
    """
    Обновить вид спорта.

    Args:
        sport_id: ID вида спорта
        sport_update: Данные для обновления
        repo: Репозиторий видов спорта

    Returns:
        Обновленный вид спорта

    Raises:
        HTTPException: Если вид спорта не найден
    """
    sport = await repo.get_by_id(sport_id)
    if not sport:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Вид спорта не найден",
        )
    return await repo.update_sport(sport, sport_update)


@router.delete("/{sport_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_sport(sport_id: int, repo: SportRepoDep):
    """
    Удалить вид спорта.

    Args:
        sport_id: ID вида спорта
        repo: Репозиторий видов спорта

    Raises:
        HTTPException: Если вид спорта не найден
    """
    sport = await repo.get_by_id(sport_id)
    if not sport:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Вид спорта не найден",
        )
    await repo.delete_sport(sport)
