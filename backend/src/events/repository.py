"""
Репозиторий для работы с мероприятиями, участниками и заявками.
"""

from datetime import UTC, datetime

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.events.models import Event, EventApplication, EventParticipant
from src.events.schemas import EventApplicationCreate, EventCreate, EventUpdate
from src.repositories.base import BaseRepository
from src.sports.models import Sport


class EventRepository(BaseRepository[Event]):
    """
    Репозиторий для операций с мероприятиями.

    Наследует базовые CRUD-операции и добавляет специфичные методы
    для работы с Event (фильтрация, участники, заявки и т.п.).
    """

    def __init__(self, session: AsyncSession) -> None:
        """
        Инициализация репозитория мероприятий.

        Args:
            session: Асинхронная сессия БД
        """
        super().__init__(session, Event)

    async def _resolve_sport_id(self, sport_type: str | None) -> int | None:
        """
        Найти sport_id по названию вида спорта.

        Args:
            sport_type: Название вида спорта

        Returns:
            ID вида спорта или None, если не найден
        """
        if not sport_type:
            return None
        query = select(Sport).where(Sport.name == sport_type)
        result = await self.session.execute(query)
        sport = result.scalar_one_or_none()
        return sport.id if sport else None

    # --- Основные операции с Event ---

    async def get_by_id(self, event_id: int) -> Event | None:
        """
        Получить мероприятие по ID.

        Args:
            event_id: ID мероприятия

        Returns:
            Event или None
        """
        return await self.get(event_id)

    async def list_events(
        self,
        skip: int = 0,
        limit: int = 100,
        creator_id: int | None = None,
        sport_type: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> list[Event]:
        """
        Получить список мероприятий с фильтрацией.

        Args:
            skip: Сколько записей пропустить
            limit: Максимальное количество записей
            creator_id: Фильтр по создателю (опционально)
            sport_type: Фильтр по виду спорта (опционально)
            date_from: Фильтр по дате от (опционально)
            date_to: Фильтр по дате до (опционально)

        Returns:
            Список мероприятий
        """
        query = select(Event)
        conditions = []

        if creator_id is not None:
            conditions.append(Event.creator_id == creator_id)
        if sport_type is not None:
            query = query.join(Sport, Event.sport_id == Sport.id)
            conditions.append(Sport.name == sport_type)
        if date_from is not None:
            conditions.append(Event.date >= date_from)
        if date_to is not None:
            conditions.append(Event.date <= date_to)

        if conditions:
            query = query.where(and_(*conditions))

        query = query.order_by(Event.date.asc()).offset(skip).limit(limit)
        return await self._execute_query(query)

    async def count_events(self, creator_id: int | None = None) -> int:
        """
        Получить количество мероприятий.

        Args:
            creator_id: Фильтр по создателю (опционально)

        Returns:
            Количество мероприятий
        """
        query = select(func.count(Event.id))
        if creator_id is not None:
            query = query.where(Event.creator_id == creator_id)
        result = await self.session.execute(query)
        return result.scalar() or 0

    async def create_event(self, event_data: EventCreate) -> Event:
        """
        Создать новое мероприятие.

        Args:
            event_data: Данные для создания мероприятия

        Returns:
            Созданное мероприятие
        """
        payload = event_data.model_dump()
        sport_type = payload.pop("sport_type", None)
        payload["sport_id"] = await self._resolve_sport_id(sport_type)
        event = Event(**payload)
        return await self.add(event)

    async def update_event(self, event: Event, event_data: EventUpdate) -> Event:
        """
        Обновить данные мероприятия.

        Args:
            event: Существующее мероприятие
            event_data: Данные для обновления

        Returns:
            Обновлённое мероприятие
        """
        update_data = event_data.model_dump(exclude_unset=True)
        if "sport_type" in update_data:
            sport_type = update_data.pop("sport_type")
            update_data["sport_id"] = await self._resolve_sport_id(sport_type)
        return await self.update(event, update_data)

    async def delete_event(self, event: Event) -> None:
        """
        Удалить мероприятие.

        Args:
            event: Мероприятие для удаления
        """
        await self.delete(event)

    # --- Операции с участниками ---

    async def get_participant(
        self,
        event_id: int,
        user_id: int,
    ) -> EventParticipant | None:
        """
        Получить запись об участии.

        Args:
            event_id: ID мероприятия
            user_id: ID пользователя

        Returns:
            EventParticipant или None
        """
        query = select(EventParticipant).where(
            EventParticipant.event_id == event_id,
            EventParticipant.user_id == user_id,
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def add_participant(
        self,
        event_id: int,
        user_id: int,
    ) -> EventParticipant | None:
        """
        Добавить участника в мероприятие.

        Args:
            event_id: ID мероприятия
            user_id: ID пользователя

        Returns:
            EventParticipant или None если уже участвует
        """
        existing = await self.get_participant(event_id, user_id)
        if existing:
            return None

        participant = EventParticipant(event_id=event_id, user_id=user_id)
        self.session.add(participant)
        await self.session.commit()
        await self.session.refresh(participant)
        return participant

    async def remove_participant(
        self,
        event_id: int,
        user_id: int,
    ) -> bool:
        """
        Удалить участника из мероприятия.

        Args:
            event_id: ID мероприятия
            user_id: ID пользователя

        Returns:
            True если удалён, False если не найден
        """
        participant = await self.get_participant(event_id, user_id)
        if not participant:
            return False
        await self.session.delete(participant)
        await self.session.commit()
        return True

    async def list_participants(
        self,
        event_id: int,
        skip: int = 0,
        limit: int = 100,
    ) -> list[EventParticipant]:
        """
        Получить участников мероприятия.

        Args:
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
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count_participants(self, event_id: int) -> int:
        """
        Получить количество участников мероприятия.

        Args:
            event_id: ID мероприятия

        Returns:
            Количество участников
        """
        query = select(func.count(EventParticipant.id)).where(EventParticipant.event_id == event_id)
        result = await self.session.execute(query)
        return result.scalar() or 0

    async def list_user_events(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Event]:
        """
        Получить мероприятия, в которых участвует пользователь.

        Args:
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
        return await self._execute_query(query)

    # --- Операции с заявками ---

    async def get_application(
        self,
        event_id: int,
        user_id: int,
    ) -> EventApplication | None:
        """
        Получить заявку по event_id и user_id.

        Args:
            event_id: ID мероприятия
            user_id: ID пользователя

        Returns:
            EventApplication или None
        """
        query = select(EventApplication).where(
            EventApplication.event_id == event_id,
            EventApplication.user_id == user_id,
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_application_by_id(
        self,
        application_id: int,
    ) -> EventApplication | None:
        """
        Получить заявку по ID.

        Args:
            application_id: ID заявки

        Returns:
            EventApplication или None
        """
        return await self.session.get(EventApplication, application_id)

    async def create_application(
        self,
        application_data: EventApplicationCreate,
    ) -> EventApplication:
        """
        Создать заявку на участие в мероприятии.

        Args:
            application_data: Данные заявки

        Returns:
            Созданная заявка

        Raises:
            ValueError: Если заявка уже существует или пользователь — создатель события
        """
        existing = await self.get_application(
            application_data.event_id,
            application_data.user_id,
        )
        if existing:
            raise ValueError("Заявка уже существует")

        event = await self.get_by_id(application_data.event_id)
        if event and event.creator_id == application_data.user_id:
            raise ValueError("Создатель события не может подать заявку на своё событие")

        application = EventApplication(
            **application_data.model_dump(),
            status="pending",
        )
        self.session.add(application)
        await self.session.commit()
        await self.session.refresh(application)
        return application

    async def list_event_applications(
        self,
        event_id: int,
        status: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[EventApplication]:
        """
        Получить заявки на мероприятие.

        Args:
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
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def list_user_applications(
        self,
        user_id: int,
        status: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[EventApplication]:
        """
        Получить заявки пользователя.

        Args:
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
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update_application_status(
        self,
        application: EventApplication,
        status: str,
    ) -> EventApplication:
        """
        Обновить статус заявки (approve/reject).

        При одобрении заявки автоматически добавляет участника.

        Args:
            application: Объект заявки
            status: Новый статус (approved или rejected)

        Returns:
            Обновлённая заявка

        Raises:
            ValueError: Если статус некорректен
        """
        if status not in ("approved", "rejected"):
            raise ValueError("Статус должен быть 'approved' или 'rejected'")

        application.status = status
        application.reviewed_at = datetime.now(UTC)

        # Если заявка одобрена, добавляем участника
        if status == "approved":
            existing_participant = await self.get_participant(
                application.event_id,
                application.user_id,
            )
            if not existing_participant:
                participant = EventParticipant(
                    event_id=application.event_id,
                    user_id=application.user_id,
                )
                self.session.add(participant)

        await self.session.commit()
        await self.session.refresh(application)
        return application

    async def delete_application(self, application: EventApplication) -> None:
        """
        Удалить заявку.

        Args:
            application: Объект заявки
        """
        await self.session.delete(application)
        await self.session.commit()
