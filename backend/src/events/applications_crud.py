"""
CRUD операции для заявок на участие в мероприятиях.
"""

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.events.models import Event, EventApplication, EventParticipant
from src.events.schemas import EventApplicationCreate


async def create_application(
    session: AsyncSession,
    application_data: EventApplicationCreate,
) -> EventApplication:
    """
    Создать заявку на участие в мероприятии.

    Args:
        session: Сессия БД
        application_data: Данные заявки

    Returns:
        Созданная заявка
    """
    # Проверяем, нет ли уже заявки или участия
    existing = await get_application(session, application_data.event_id, application_data.user_id)
    if existing:
        raise ValueError("Заявка уже существует")

    # Проверяем, не является ли пользователь создателем события
    event = await session.get(Event, application_data.event_id)
    if event and event.creator_id == application_data.user_id:
        raise ValueError("Создатель события не может подать заявку на своё событие")

    application = EventApplication(**application_data.model_dump(), status="pending")
    session.add(application)
    await session.commit()
    await session.refresh(application)
    return application


async def get_application(
    session: AsyncSession,
    event_id: int,
    user_id: int,
) -> EventApplication | None:
    """
    Получить заявку по event_id и user_id.

    Args:
        session: Сессия БД
        event_id: ID мероприятия
        user_id: ID пользователя

    Returns:
        EventApplication или None
    """
    query = select(EventApplication).where(
        EventApplication.event_id == event_id,
        EventApplication.user_id == user_id,
    )
    result = await session.execute(query)
    return result.scalar_one_or_none()


async def get_application_by_id(
    session: AsyncSession, application_id: int
) -> EventApplication | None:
    """
    Получить заявку по ID.

    Args:
        session: Сессия БД
        application_id: ID заявки

    Returns:
        EventApplication или None
    """
    return await session.get(EventApplication, application_id)


async def get_event_applications(
    session: AsyncSession,
    event_id: int,
    status: str | None = None,
    skip: int = 0,
    limit: int = 100,
) -> list[EventApplication]:
    """
    Получить заявки на мероприятие.

    Args:
        session: Сессия БД
        event_id: ID мероприятия
        status: Фильтр по статусу (pending, approved, rejected)
        skip: Сколько записей пропустить
        limit: Максимальное количество записей

    Returns:
        Список заявок
    """
    query = select(EventApplication).where(EventApplication.event_id == event_id)

    if status:
        query = query.where(EventApplication.status == status)

    query = query.order_by(EventApplication.applied_at.desc()).offset(skip).limit(limit)
    result = await session.execute(query)
    return list(result.scalars().all())


async def get_user_applications(
    session: AsyncSession,
    user_id: int,
    status: str | None = None,
    skip: int = 0,
    limit: int = 100,
) -> list[EventApplication]:
    """
    Получить заявки пользователя.

    Args:
        session: Сессия БД
        user_id: ID пользователя
        status: Фильтр по статусу
        skip: Сколько записей пропустить
        limit: Максимальное количество записей

    Returns:
        Список заявок
    """
    query = select(EventApplication).where(EventApplication.user_id == user_id)

    if status:
        query = query.where(EventApplication.status == status)

    query = query.order_by(EventApplication.applied_at.desc()).offset(skip).limit(limit)
    result = await session.execute(query)
    return list(result.scalars().all())


async def update_application_status(
    session: AsyncSession,
    application: EventApplication,
    status: str,
) -> EventApplication:
    """
    Обновить статус заявки (approve/reject).

    Args:
        session: Сессия БД
        application: Объект заявки
        status: Новый статус (approved или rejected)

    Returns:
        Обновлённая заявка
    """
    if status not in ("approved", "rejected"):
        raise ValueError("Статус должен быть 'approved' или 'rejected'")

    application.status = status
    application.reviewed_at = datetime.now(UTC)

    # Если заявка одобрена, добавляем участника
    if status == "approved":
        # Проверяем, не добавлен ли уже участник
        existing_participant = await session.execute(
            select(EventParticipant).where(
                EventParticipant.event_id == application.event_id,
                EventParticipant.user_id == application.user_id,
            )
        )
        if not existing_participant.scalar_one_or_none():
            participant = EventParticipant(
                event_id=application.event_id,
                user_id=application.user_id,
            )
            session.add(participant)

    await session.commit()
    await session.refresh(application)
    return application


async def delete_application(session: AsyncSession, application: EventApplication) -> None:
    """
    Удалить заявку.

    Args:
        session: Сессия БД
        application: Объект заявки
    """
    await session.delete(application)
    await session.commit()
