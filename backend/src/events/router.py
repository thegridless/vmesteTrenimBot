"""
API роутер для мероприятий.
"""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_session
from src.events import crud
from src.events.applications_crud import (
    create_application,
    get_application_by_id,
    get_event_applications,
    get_user_applications,
    update_application_status,
)
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
from src.users.crud import get_user_by_id

router = APIRouter(prefix="/events", tags=["events"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


@router.get("/", response_model=list[EventResponse])
async def get_events(
    session: SessionDep,
    skip: int = 0,
    limit: int = 100,
    creator_id: int | None = None,
    sport_type: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
):
    """Получить список мероприятий с фильтрацией."""
    return await crud.get_events(
        session,
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
    session: SessionDep,
):
    """Поиск мероприятий по параметрам."""
    return await crud.get_events(
        session,
        skip=search_params.skip,
        limit=search_params.limit,
        sport_type=search_params.sport_type,
        date_from=search_params.date_from,
        date_to=search_params.date_to,
    )


@router.get("/{event_id}", response_model=EventWithParticipants)
async def get_event(event_id: int, session: SessionDep):
    """Получить мероприятие по ID с количеством участников."""
    event = await crud.get_event_by_id(session, event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Мероприятие не найдено",
        )
    participants_count = await crud.get_participants_count(session, event_id)
    return EventWithParticipants(
        **EventResponse.model_validate(event).model_dump(),
        participants_count=participants_count,
    )


@router.post("/", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
async def create_event(event_data: EventCreate, session: SessionDep):
    """Создать новое мероприятие."""
    # Проверяем существование создателя
    creator = await get_user_by_id(session, event_data.creator_id)
    if not creator:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Создатель не найден",
        )
    return await crud.create_event(session, event_data)


@router.patch("/{event_id}", response_model=EventResponse)
async def update_event(event_id: int, event_data: EventUpdate, session: SessionDep):
    """Обновить данные мероприятия."""
    event = await crud.get_event_by_id(session, event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Мероприятие не найдено",
        )
    return await crud.update_event(session, event, event_data)


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(event_id: int, session: SessionDep):
    """Удалить мероприятие."""
    event = await crud.get_event_by_id(session, event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Мероприятие не найдено",
        )
    await crud.delete_event(session, event)


# --- Участники ---


@router.get("/{event_id}/participants", response_model=list[ParticipantResponse])
async def get_event_participants(
    event_id: int,
    session: SessionDep,
    skip: int = 0,
    limit: int = 100,
):
    """Получить участников мероприятия."""
    event = await crud.get_event_by_id(session, event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Мероприятие не найдено",
        )
    return await crud.get_event_participants(session, event_id, skip=skip, limit=limit)


@router.post(
    "/{event_id}/participants/{user_id}",
    response_model=ParticipantResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_participant(event_id: int, user_id: int, session: SessionDep):
    """Добавить участника в мероприятие."""
    event = await crud.get_event_by_id(session, event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Мероприятие не найдено",
        )
    user = await get_user_by_id(session, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден",
        )
    participant = await crud.add_participant(session, event_id, user_id)
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
async def remove_participant(event_id: int, user_id: int, session: SessionDep):
    """Удалить участника из мероприятия."""
    removed = await crud.remove_participant(session, event_id, user_id)
    if not removed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Участник не найден",
        )


# --- События пользователя ---


@router.get("/user/{user_id}", response_model=list[EventResponse])
async def get_user_events(
    user_id: int,
    session: SessionDep,
    skip: int = 0,
    limit: int = 100,
):
    """Получить мероприятия, в которых участвует пользователь."""
    user = await get_user_by_id(session, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден",
        )
    return await crud.get_user_events(session, user_id, skip=skip, limit=limit)


# --- Заявки на участие ---


@router.post(
    "/{event_id}/apply",
    response_model=EventApplicationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def apply_to_event(event_id: int, user_id: int, session: SessionDep):
    """Подать заявку на участие в мероприятии."""
    event = await crud.get_event_by_id(session, event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Мероприятие не найдено",
        )
    user = await get_user_by_id(session, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден",
        )

    try:
        application = await create_application(
            session,
            EventApplicationCreate(event_id=event_id, user_id=user_id),
        )
        return application
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/{event_id}/applications", response_model=list[EventApplicationResponse])
async def get_event_applications_list(
    event_id: int,
    session: SessionDep,
    status: str | None = None,
    skip: int = 0,
    limit: int = 100,
):
    """Получить заявки на мероприятие."""
    event = await crud.get_event_by_id(session, event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Мероприятие не найдено",
        )
    return await get_event_applications(session, event_id, status=status, skip=skip, limit=limit)


@router.get("/applications/user/{user_id}", response_model=list[EventApplicationResponse])
async def get_user_applications_list(
    user_id: int,
    session: SessionDep,
    status: str | None = None,
    skip: int = 0,
    limit: int = 100,
):
    """Получить заявки пользователя."""
    user = await get_user_by_id(session, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден",
        )
    return await get_user_applications(session, user_id, status=status, skip=skip, limit=limit)


@router.patch("/applications/{application_id}", response_model=EventApplicationResponse)
async def review_application(
    application_id: int,
    application_update: EventApplicationUpdate,
    session: SessionDep,
):
    """Рассмотреть заявку (подтвердить/отклонить)."""
    application = await get_application_by_id(session, application_id)
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Заявка не найдена",
        )

    try:
        updated = await update_application_status(session, application, application_update.status)
        return updated
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
