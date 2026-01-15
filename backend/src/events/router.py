"""
API роутер для мероприятий.
"""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_session
from src.events.repository import EventRepository
from src.events.schemas import (
    EventApplicationCreate,
    EventApplicationResponse,
    EventApplicationUpdate,
    EventCreate,
    EventResponse,
    EventSearchParams,
    EventUpdate,
    EventWithParticipants,
    ParticipantResponse,
)
from src.users.repository import UserRepository

router = APIRouter(prefix="/events", tags=["events"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


def get_event_repository(session: SessionDep) -> EventRepository:
    """
    Dependency для получения репозитория мероприятий.

    Args:
        session: Асинхронная сессия БД

    Returns:
        Экземпляр EventRepository
    """
    return EventRepository(session)


def get_user_repository(session: SessionDep) -> UserRepository:
    """
    Dependency для получения репозитория пользователей.

    Args:
        session: Асинхронная сессия БД

    Returns:
        Экземпляр UserRepository
    """
    return UserRepository(session)


EventRepoDep = Annotated[EventRepository, Depends(get_event_repository)]
UserRepoDep = Annotated[UserRepository, Depends(get_user_repository)]


@router.get("/", response_model=list[EventResponse])
async def get_events(
    repo: EventRepoDep,
    skip: int = 0,
    limit: int = 100,
    creator_id: int | None = None,
    sport_type: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
):
    """Получить список мероприятий с фильтрацией."""
    return await repo.list_events(
        skip=skip,
        limit=limit,
        creator_id=creator_id,
        sport_type=sport_type,
        date_from=date_from,
        date_to=date_to,
    )


@router.post("/search", response_model=list[EventResponse])
async def search_events(
    search_params: EventSearchParams,
    repo: EventRepoDep,
):
    """Поиск мероприятий по параметрам."""
    return await repo.list_events(
        skip=search_params.skip,
        limit=search_params.limit,
        sport_type=search_params.sport_type,
        date_from=search_params.date_from,
        date_to=search_params.date_to,
    )


@router.get("/{event_id}", response_model=EventWithParticipants)
async def get_event(event_id: int, repo: EventRepoDep):
    """Получить мероприятие по ID с количеством участников."""
    event = await repo.get_by_id(event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Мероприятие не найдено",
        )
    participants_count = await repo.count_participants(event_id)
    return EventWithParticipants(
        **EventResponse.model_validate(event).model_dump(),
        participants_count=participants_count,
    )


@router.post("/", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
async def create_event(
    event_data: EventCreate,
    repo: EventRepoDep,
    user_repo: UserRepoDep,
):
    """Создать новое мероприятие."""
    creator = await user_repo.get_by_id(event_data.creator_id)
    if not creator:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Создатель не найден",
        )
    return await repo.create_event(event_data)


@router.patch("/{event_id}", response_model=EventResponse)
async def update_event(
    event_id: int,
    event_data: EventUpdate,
    repo: EventRepoDep,
):
    """Обновить данные мероприятия."""
    event = await repo.get_by_id(event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Мероприятие не найдено",
        )
    return await repo.update_event(event, event_data)


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(event_id: int, repo: EventRepoDep):
    """Удалить мероприятие."""
    event = await repo.get_by_id(event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Мероприятие не найдено",
        )
    await repo.delete_event(event)


# --- Участники ---


@router.get("/{event_id}/participants", response_model=list[ParticipantResponse])
async def get_event_participants(
    event_id: int,
    repo: EventRepoDep,
    skip: int = 0,
    limit: int = 100,
):
    """Получить участников мероприятия."""
    event = await repo.get_by_id(event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Мероприятие не найдено",
        )
    return await repo.list_participants(event_id, skip=skip, limit=limit)


@router.post(
    "/{event_id}/participants/{user_id}",
    response_model=ParticipantResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_participant(
    event_id: int,
    user_id: int,
    repo: EventRepoDep,
    user_repo: UserRepoDep,
):
    """Добавить участника в мероприятие."""
    event = await repo.get_by_id(event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Мероприятие не найдено",
        )
    user = await user_repo.get_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден",
        )
    participant = await repo.add_participant(event_id, user_id)
    if not participant:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь уже участвует в мероприятии",
        )
    return participant


@router.delete(
    "/{event_id}/participants/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_participant(event_id: int, user_id: int, repo: EventRepoDep):
    """Удалить участника из мероприятия."""
    removed = await repo.remove_participant(event_id, user_id)
    if not removed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Участник не найден",
        )


# --- События пользователя ---


@router.get("/user/{user_id}", response_model=list[EventResponse])
async def get_user_events(
    user_id: int,
    repo: EventRepoDep,
    user_repo: UserRepoDep,
    skip: int = 0,
    limit: int = 100,
):
    """Получить мероприятия, в которых участвует пользователь."""
    user = await user_repo.get_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден",
        )
    return await repo.list_user_events(user_id, skip=skip, limit=limit)


# --- Заявки на участие ---


@router.post(
    "/{event_id}/apply",
    response_model=EventApplicationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def apply_to_event(
    event_id: int,
    user_id: int,
    repo: EventRepoDep,
    user_repo: UserRepoDep,
):
    """Подать заявку на участие в мероприятии."""
    event = await repo.get_by_id(event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Мероприятие не найдено",
        )
    user = await user_repo.get_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден",
        )

    try:
        application = await repo.create_application(
            EventApplicationCreate(event_id=event_id, user_id=user_id),
        )
        return application
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


@router.get("/{event_id}/applications", response_model=list[EventApplicationResponse])
async def get_event_applications_list(
    event_id: int,
    repo: EventRepoDep,
    status_filter: str | None = None,
    skip: int = 0,
    limit: int = 100,
):
    """Получить заявки на мероприятие."""
    event = await repo.get_by_id(event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Мероприятие не найдено",
        )
    return await repo.list_event_applications(
        event_id,
        status=status_filter,
        skip=skip,
        limit=limit,
    )


@router.get("/applications/user/{user_id}", response_model=list[EventApplicationResponse])
async def get_user_applications_list(
    user_id: int,
    repo: EventRepoDep,
    user_repo: UserRepoDep,
    status_filter: str | None = None,
    skip: int = 0,
    limit: int = 100,
):
    """Получить заявки пользователя."""
    user = await user_repo.get_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден",
        )
    return await repo.list_user_applications(
        user_id,
        status=status_filter,
        skip=skip,
        limit=limit,
    )


@router.patch("/applications/{application_id}", response_model=EventApplicationResponse)
async def review_application(
    application_id: int,
    application_update: EventApplicationUpdate,
    repo: EventRepoDep,
):
    """Рассмотреть заявку (подтвердить/отклонить)."""
    application = await repo.get_application_by_id(application_id)
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Заявка не найдена",
        )

    try:
        updated = await repo.update_application_status(application, application_update.status)
        return updated
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
