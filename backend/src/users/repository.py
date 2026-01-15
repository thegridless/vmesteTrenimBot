"""
Репозиторий для работы с пользователями.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.repositories.base import BaseRepository
from src.users.models import User
from src.users.schemas import UserCreate, UserUpdate


class UserRepository(BaseRepository[User]):
    """
    Репозиторий для операций с пользователями.

    Наследует базовые CRUD-операции и добавляет специфичные методы
    для работы с User (поиск по telegram_id, get_or_create и т.п.).
    """

    def __init__(self, session: AsyncSession) -> None:
        """
        Инициализация репозитория пользователей.

        Args:
            session: Асинхронная сессия БД
        """
        super().__init__(session, User)

    async def get_by_id(self, user_id: int) -> User | None:
        """
        Получить пользователя по ID.

        Args:
            user_id: Первичный ключ пользователя

        Returns:
            User или None
        """
        return await self.get(user_id)

    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        """
        Получить пользователя по Telegram ID.

        Args:
            telegram_id: ID пользователя в Telegram

        Returns:
            User или None
        """
        query = select(User).where(User.telegram_id == telegram_id)
        return await self._execute_scalar(query)

    async def list_users(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> list[User]:
        """
        Получить список пользователей с пагинацией.

        Args:
            skip: Сколько записей пропустить
            limit: Максимальное количество записей

        Returns:
            Список пользователей
        """
        return await self.list(skip=skip, limit=limit)

    async def create_user(self, user_data: UserCreate) -> User:
        """
        Создать нового пользователя.

        Args:
            user_data: Данные для создания пользователя

        Returns:
            Созданный пользователь
        """
        # Исключаем sports, т.к. это many-to-many связь
        data = user_data.model_dump(exclude={"sports"})
        user = User(**data)
        return await self.add(user)

    async def update_user(self, user: User, user_data: UserUpdate) -> User:
        """
        Обновить данные пользователя.

        Args:
            user: Существующий пользователь
            user_data: Данные для обновления

        Returns:
            Обновлённый пользователь
        """
        # Исключаем sports и неустановленные поля
        update_data = user_data.model_dump(exclude_unset=True, exclude={"sports"})
        return await self.update(user, update_data)

    async def delete_user(self, user: User) -> None:
        """
        Удалить пользователя.

        Args:
            user: Пользователь для удаления
        """
        await self.delete(user)

    async def get_or_create_user(self, user_data: UserCreate) -> tuple[User, bool]:
        """
        Получить существующего пользователя или создать нового.

        Args:
            user_data: Данные пользователя

        Returns:
            Кортеж (User, created: bool) — created=True если создан новый
        """
        user = await self.get_by_telegram_id(user_data.telegram_id)
        if user:
            return user, False
        user = await self.create_user(user_data)
        return user, True
