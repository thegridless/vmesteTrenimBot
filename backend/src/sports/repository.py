"""
Репозиторий для работы с видами спорта.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.base import BaseRepository
from src.sports.models import Sport
from src.sports.schemas import SportCreate, SportUpdate


class SportRepository(BaseRepository[Sport]):
    """
    Репозиторий для операций с видами спорта.

    Наследует базовые CRUD-операции и добавляет специфичные методы
    для работы со Sport (поиск по имени, фильтрация по активности).
    """

    def __init__(self, session: AsyncSession) -> None:
        """
        Инициализация репозитория видов спорта.

        Args:
            session: Асинхронная сессия БД
        """
        super().__init__(session, Sport)

    async def get_by_id(self, sport_id: int) -> Sport | None:
        """
        Получить вид спорта по ID.

        Args:
            sport_id: ID вида спорта

        Returns:
            Sport или None
        """
        return await self.get(sport_id)

    async def get_by_name(self, name: str) -> Sport | None:
        """
        Получить вид спорта по названию.

        Args:
            name: Название вида спорта

        Returns:
            Sport или None
        """
        query = select(Sport).where(Sport.name == name)
        return await self._execute_scalar(query)

    async def list_sports(
        self,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = False,
    ) -> list[Sport]:
        """
        Получить список видов спорта с фильтрацией.

        Args:
            skip: Сколько записей пропустить
            limit: Максимальное количество записей
            active_only: Только активные виды спорта

        Returns:
            Список видов спорта
        """
        query = select(Sport)
        if active_only:
            query = query.where(Sport.active.is_(True))
        query = query.offset(skip).limit(limit)
        return await self._execute_query(query)

    async def create_sport(self, sport_data: SportCreate) -> Sport:
        """
        Создать новый вид спорта.

        Args:
            sport_data: Данные для создания

        Returns:
            Созданный вид спорта
        """
        sport = Sport(**sport_data.model_dump())
        return await self.add(sport)

    async def update_sport(self, sport: Sport, sport_data: SportUpdate) -> Sport:
        """
        Обновить вид спорта.

        Args:
            sport: Существующий вид спорта
            sport_data: Данные для обновления

        Returns:
            Обновлённый вид спорта
        """
        update_data = sport_data.model_dump(exclude_unset=True)
        return await self.update(sport, update_data)

    async def delete_sport(self, sport: Sport) -> None:
        """
        Удалить вид спорта.

        Args:
            sport: Вид спорта для удаления
        """
        await self.delete(sport)
