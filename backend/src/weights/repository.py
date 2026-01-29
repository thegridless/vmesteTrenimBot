"""
Репозиторий для работы с весами пользователей.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.base import BaseRepository
from src.weights.models import Weight
from src.weights.schemas import WeightCreate


class WeightRepository(BaseRepository[Weight]):
    """
    Репозиторий для операций с весами.

    Наследует базовые CRUD-операции и добавляет специфичные методы.
    """

    def __init__(self, session: AsyncSession) -> None:
        """
        Инициализация репозитория весов.

        Args:
            session: Асинхронная сессия БД
        """
        super().__init__(session, Weight)

    async def create_weight(self, weight_data: WeightCreate) -> Weight:
        """
        Создать новую запись веса.

        Args:
            weight_data: Данные для создания записи веса

        Returns:
            Созданная запись веса
        """
        weight = Weight(**weight_data.model_dump())
        return await self.add(weight)

    async def list_user_exercises(self, user_id: int) -> list[str]:
        """
        Получить список уникальных упражнений пользователя.

        Args:
            user_id: ID пользователя

        Returns:
            Список названий упражнений
        """
        query = (
            select(Weight.exercise)
            .where(Weight.user_id == user_id)
            .distinct()
            .order_by(Weight.exercise.asc())
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def list_progress(
        self,
        user_id: int,
        exercise: str,
        limit: int = 5,
    ) -> list[Weight]:
        """
        Получить последние записи веса по упражнению.

        Args:
            user_id: ID пользователя
            exercise: Название упражнения
            limit: Количество записей

        Returns:
            Список записей веса
        """
        query = (
            select(Weight)
            .where(Weight.user_id == user_id, Weight.exercise == exercise)
            .order_by(Weight.date.desc())
            .limit(limit)
        )
        return await self._execute_query(query)
