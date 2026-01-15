"""
Базовый репозиторий с общими CRUD-операциями.
Обеспечивает типизированный доступ к моделям через AsyncSession.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Generic, TypeVar

if TYPE_CHECKING:
    from sqlalchemy import Select

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import Base

# Тип модели, унаследованной от Base
TModel = TypeVar("TModel", bound=Base)


class BaseRepository(Generic[TModel]):  # noqa: UP046
    """
    Базовый репозиторий с типизированными CRUD-операциями.

    Attributes:
        session: Асинхронная сессия SQLAlchemy
        model: Класс модели SQLAlchemy

    Пример использования:
        class UserRepository(BaseRepository[User]):
            def __init__(self, session: AsyncSession):
                super().__init__(session, User)
    """

    def __init__(self, session: AsyncSession, model: type[TModel]) -> None:
        """
        Инициализация репозитория.

        Args:
            session: Асинхронная сессия БД
            model: Класс SQLAlchemy-модели
        """
        self.session = session
        self.model = model

    async def get(self, entity_id: int) -> TModel | None:
        """
        Получить сущность по первичному ключу.

        Args:
            entity_id: Первичный ключ (id)

        Returns:
            Экземпляр модели или None
        """
        return await self.session.get(self.model, entity_id)

    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
        order_by: Any | None = None,
    ) -> list[TModel]:
        """
        Получить список сущностей с пагинацией.

        Args:
            skip: Сколько записей пропустить
            limit: Максимальное количество записей
            order_by: Колонка или выражение для сортировки (опционально)

        Returns:
            Список экземпляров модели
        """
        query = select(self.model)
        if order_by is not None:
            query = query.order_by(order_by)
        query = query.offset(skip).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def add(self, entity: TModel) -> TModel:
        """
        Добавить новую сущность в БД.

        Args:
            entity: Экземпляр модели для сохранения

        Returns:
            Сохранённый экземпляр с обновлёнными полями (id, created_at и т.п.)
        """
        self.session.add(entity)
        await self.session.commit()
        await self.session.refresh(entity)
        return entity

    async def update(self, entity: TModel, update_data: dict[str, Any]) -> TModel:
        """
        Обновить поля сущности.

        Args:
            entity: Существующий экземпляр модели
            update_data: Словарь с полями для обновления

        Returns:
            Обновлённый экземпляр модели
        """
        for field, value in update_data.items():
            setattr(entity, field, value)
        await self.session.commit()
        await self.session.refresh(entity)
        return entity

    async def delete(self, entity: TModel) -> None:
        """
        Удалить сущность из БД.

        Args:
            entity: Экземпляр модели для удаления
        """
        await self.session.delete(entity)
        await self.session.commit()

    async def count(self) -> int:
        """
        Получить общее количество записей в таблице.

        Returns:
            Количество записей
        """
        query = select(func.count()).select_from(self.model)
        result = await self.session.execute(query)
        return result.scalar() or 0

    async def exists(self, entity_id: int) -> bool:
        """
        Проверить существование сущности по id.

        Args:
            entity_id: Первичный ключ

        Returns:
            True если существует, False иначе
        """
        entity = await self.get(entity_id)
        return entity is not None

    def _base_query(self) -> Select[tuple[TModel]]:
        """
        Базовый запрос для построения сложных выборок.

        Returns:
            Select-запрос для модели
        """
        return select(self.model)

    async def _execute_query(self, query: Select[tuple[TModel]]) -> list[TModel]:
        """
        Выполнить произвольный select-запрос.

        Args:
            query: Подготовленный Select-запрос

        Returns:
            Список результатов
        """
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def _execute_scalar(self, query: Select[tuple[TModel]]) -> TModel | None:
        """
        Выполнить запрос и получить один результат или None.

        Args:
            query: Подготовленный Select-запрос

        Returns:
            Один результат или None
        """
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
