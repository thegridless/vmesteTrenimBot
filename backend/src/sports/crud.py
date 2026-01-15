"""
CRUD операции для видов спорта.
"""

from sports.models import Sport
from sports.schemas import SportCreate, SportUpdate
from sqlalchemy.orm import Session


def get_sport(db: Session, sport_id: int) -> Sport | None:
    """
    Получить вид спорта по ID.

    Args:
        db: Сессия БД
        sport_id: ID вида спорта

    Returns:
        Вид спорта или None
    """
    return db.query(Sport).filter(Sport.id == sport_id).first()


def get_sport_by_name(db: Session, name: str) -> Sport | None:
    """
    Получить вид спорта по названию.

    Args:
        db: Сессия БД
        name: Название вида спорта

    Returns:
        Вид спорта или None
    """
    return db.query(Sport).filter(Sport.name == name).first()


def get_sports(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    active_only: bool = False,
) -> list[Sport]:
    """
    Получить список видов спорта.

    Args:
        db: Сессия БД
        skip: Сколько пропустить
        limit: Максимум записей
        active_only: Только активные виды спорта

    Returns:
        Список видов спорта
    """
    query = db.query(Sport)
    if active_only:
        query = query.filter(Sport.active.is_(True))
    return query.offset(skip).limit(limit).all()


def create_sport(db: Session, sport: SportCreate) -> Sport:
    """
    Создать новый вид спорта.

    Args:
        db: Сессия БД
        sport: Данные для создания

    Returns:
        Созданный вид спорта
    """
    db_sport = Sport(**sport.model_dump())
    db.add(db_sport)
    db.commit()
    db.refresh(db_sport)
    return db_sport


def update_sport(db: Session, sport_id: int, sport_update: SportUpdate) -> Sport | None:
    """
    Обновить вид спорта.

    Args:
        db: Сессия БД
        sport_id: ID вида спорта
        sport_update: Данные для обновления

    Returns:
        Обновленный вид спорта или None
    """
    db_sport = get_sport(db, sport_id)
    if not db_sport:
        return None

    update_data = sport_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_sport, field, value)

    db.commit()
    db.refresh(db_sport)
    return db_sport


def delete_sport(db: Session, sport_id: int) -> bool:
    """
    Удалить вид спорта.

    Args:
        db: Сессия БД
        sport_id: ID вида спорта

    Returns:
        True если удален, False если не найден
    """
    db_sport = get_sport(db, sport_id)
    if not db_sport:
        return False

    db.delete(db_sport)
    db.commit()
    return True
