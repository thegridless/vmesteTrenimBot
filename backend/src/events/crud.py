"""
CRUD операции для мероприятий и участников.
"""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.events.models import Event, EventParticipant
from src.events.schemas import EventCreate, EventUpdate


async def get_event_by_id(session: AsyncSession, event_id: int) -> Event | None:
    """
    Получить мероприятие по ID.

    Args:
        session: Сессия БД
        event_id: ID мероприятия

    Returns:
        Event или None
    """
    return await session.get(Event, event_id)


async def get_events(
    session: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    creator_id: int | None = None,
) -> list[Event]:
    """
    Получить список мероприятий с пагинацией.

    Args:
        session: Сессия БД
        skip: Сколько записей пропустить
        limit: Максимальное количество записей
        creator_id: Фильтр по создателю (опционально)

    Returns:
        Список мероприятий
    """
    query = select(Event)
    if creator_id is not None:
        query = query.where(Event.creator_id == creator_id)
    query = query.order_by(Event.date.desc()).offset(skip).limit(limit)
    result = await session.execute(query)
    return list(result.scalars().all())


async def get_events_count(
    session: AsyncSession,
    creator_id: int | None = None,
) -> int:
    """
    Получить количество мероприятий.

    Args:
        session: Сессия БД
        creator_id: Фильтр по создателю (опционально)

    Returns:
        Количество мероприятий
    """
    query = select(func.count(Event.id))
    if creator_id is not None:
        query = query.where(Event.creator_id == creator_id)
    result = await session.execute(query)
    return result.scalar() or 0


async def create_event(session: AsyncSession, event_data: EventCreate) -> Event:
    """
    Создать новое мероприятие.

    Args:
        session: Сессия БД
        event_data: Данные для создания мероприятия

    Returns:
        Созданное мероприятие
    """
    event = Event(**event_data.model_dump())
    session.add(event)
    await session.commit()
    await session.refresh(event)
    return event


async def update_event(
    session: AsyncSession,
    event: Event,
    event_data: EventUpdate,
) -> Event:
    """
    Обновить данные мероприятия.

    Args:
        session: Сессия БД
        event: Объект мероприятия
        event_data: Данные для обновления

    Returns:
        Обновлённое мероприятие
    """
    update_data = event_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(event, field, value)
    await session.commit()
    await session.refresh(event)
    return event


async def delete_event(session: AsyncSession, event: Event) -> None:
    """
    Удалить мероприятие.

    Args:
        session: Сессия БД
        event: Объект мероприятия
    """
    await session.delete(event)
    await session.commit()


# --- Операции с участниками ---


async def add_participant(
    session: AsyncSession,
    event_id: int,
    user_id: int,
) -> EventParticipant | None:
    """
    Добавить участника в мероприятие.

    Args:
        session: Сессия БД
        event_id: ID мероприятия
        user_id: ID пользователя

    Returns:
        EventParticipant или None если уже участвует
    """
    # Проверяем, не участвует ли уже
    existing = await get_participant(session, event_id, user_id)
    if existing:
        return None

    participant = EventParticipant(event_id=event_id, user_id=user_id)
    session.add(participant)
    await session.commit()
    await session.refresh(participant)
    return participant


async def get_participant(
    session: AsyncSession,
    event_id: int,
    user_id: int,
) -> EventParticipant | None:
    """
    Получить запись об участии.

    Args:
        session: Сессия БД
        event_id: ID мероприятия
        user_id: ID пользователя

    Returns:
        EventParticipant или None
    """
    query = select(EventParticipant).where(
        EventParticipant.event_id == event_id,
        EventParticipant.user_id == user_id,
    )
    result = await session.execute(query)
    return result.scalar_one_or_none()


async def remove_participant(
    session: AsyncSession,
    event_id: int,
    user_id: int,
) -> bool:
    """
    Удалить участника из мероприятия.

    Args:
        session: Сессия БД
        event_id: ID мероприятия
        user_id: ID пользователя

    Returns:
        True если удалён, False если не найден
    """
    participant = await get_participant(session, event_id, user_id)
    if not participant:
        return False
    await session.delete(participant)
    await session.commit()
    return True


async def get_event_participants(
    session: AsyncSession,
    event_id: int,
    skip: int = 0,
    limit: int = 100,
) -> list[EventParticipant]:
    """
    Получить участников мероприятия.

    Args:
        session: Сессия БД
        event_id: ID мероприятия
        skip: Сколько записей пропустить
        limit: Максимальное количество записей

    Returns:
        Список участников
    """
    query = (
        select(EventParticipant)
        .where(EventParticipant.event_id == event_id)
        .offset(skip)
        .limit(limit)
    )
    result = await session.execute(query)
    return list(result.scalars().all())


async def get_participants_count(session: AsyncSession, event_id: int) -> int:
    """
    Получить количество участников мероприятия.

    Args:
        session: Сессия БД
        event_id: ID мероприятия

    Returns:
        Количество участников
    """
    query = select(func.count(EventParticipant.id)).where(EventParticipant.event_id == event_id)
    result = await session.execute(query)
    return result.scalar() or 0


async def get_user_events(
    session: AsyncSession,
    user_id: int,
    skip: int = 0,
    limit: int = 100,
) -> list[Event]:
    """
    Получить мероприятия, в которых участвует пользователь.

    Args:
        session: Сессия БД
        user_id: ID пользователя
        skip: Сколько записей пропустить
        limit: Максимальное количество записей

    Returns:
        Список мероприятий
    """
    query = (
        select(Event)
        .join(EventParticipant)
        .where(EventParticipant.user_id == user_id)
        .order_by(Event.date.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await session.execute(query)
    return list(result.scalars().all())
