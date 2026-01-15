"""
API роутер для видов спорта.
"""

from database import get_db
from fastapi import APIRouter, Depends, HTTPException, status
from sports import crud, schemas
from sqlalchemy.orm import Session

router = APIRouter(prefix="/sports", tags=["sports"])


@router.get("", response_model=list[schemas.Sport])
def get_sports(
    skip: int = 0,
    limit: int = 100,
    active_only: bool = False,
    db: Session = Depends(get_db),
):
    """
    Получить список видов спорта.

    Args:
        skip: Сколько пропустить
        limit: Максимум записей
        active_only: Только активные виды спорта
        db: Сессия БД

    Returns:
        Список видов спорта
    """
    return crud.get_sports(db, skip=skip, limit=limit, active_only=active_only)


@router.get("/{sport_id}", response_model=schemas.Sport)
def get_sport(sport_id: int, db: Session = Depends(get_db)):
    """
    Получить вид спорта по ID.

    Args:
        sport_id: ID вида спорта
        db: Сессия БД

    Returns:
        Вид спорта

    Raises:
        HTTPException: Если вид спорта не найден
    """
    sport = crud.get_sport(db, sport_id)
    if not sport:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Вид спорта не найден",
        )
    return sport


@router.post("", response_model=schemas.Sport, status_code=status.HTTP_201_CREATED)
def create_sport(sport: schemas.SportCreate, db: Session = Depends(get_db)):
    """
    Создать новый вид спорта.

    Args:
        sport: Данные для создания
        db: Сессия БД

    Returns:
        Созданный вид спорта

    Raises:
        HTTPException: Если вид спорта с таким названием уже существует
    """
    # Проверяем, не существует ли уже такой вид спорта
    existing = crud.get_sport_by_name(db, sport.name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Вид спорта с таким названием уже существует",
        )

    return crud.create_sport(db, sport)


@router.patch("/{sport_id}", response_model=schemas.Sport)
def update_sport(
    sport_id: int,
    sport_update: schemas.SportUpdate,
    db: Session = Depends(get_db),
):
    """
    Обновить вид спорта.

    Args:
        sport_id: ID вида спорта
        sport_update: Данные для обновления
        db: Сессия БД

    Returns:
        Обновленный вид спорта

    Raises:
        HTTPException: Если вид спорта не найден
    """
    sport = crud.update_sport(db, sport_id, sport_update)
    if not sport:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Вид спорта не найден",
        )
    return sport


@router.delete("/{sport_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_sport(sport_id: int, db: Session = Depends(get_db)):
    """
    Удалить вид спорта.

    Args:
        sport_id: ID вида спорта
        db: Сессия БД

    Raises:
        HTTPException: Если вид спорта не найден
    """
    deleted = crud.delete_sport(db, sport_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Вид спорта не найден",
        )
