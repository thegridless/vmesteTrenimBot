"""
CRUD операции для пользователей.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.users.models import User
from src.users.schemas import UserCreate, UserUpdate


async def get_user_by_id(session: AsyncSession, user_id: int) -> User | None:
    """
    Получить пользователя по ID.

    Args:
        session: Сессия БД
        user_id: ID пользователя

    Returns:
        User или None
    """
    return await session.get(User, user_id)


async def get_user_by_telegram_id(session: AsyncSession, telegram_id: int) -> User | None:
    """
    Получить пользователя по Telegram ID.

    Args:
        session: Сессия БД
        telegram_id: ID пользователя в Telegram

    Returns:
        User или None
    """
    query = select(User).where(User.telegram_id == telegram_id)
    result = await session.execute(query)
    return result.scalar_one_or_none()


async def get_users(
    session: AsyncSession,
    skip: int = 0,
    limit: int = 100,
) -> list[User]:
    """
    Получить список пользователей с пагинацией.

    Args:
        session: Сессия БД
        skip: Сколько записей пропустить
        limit: Максимальное количество записей

    Returns:
        Список пользователей
    """
    query = select(User).offset(skip).limit(limit)
    result = await session.execute(query)
    return list(result.scalars().all())


async def create_user(session: AsyncSession, user_data: UserCreate) -> User:
    """
    Создать нового пользователя.

    Args:
        session: Сессия БД
        user_data: Данные для создания пользователя

    Returns:
        Созданный пользователь
    """
    user = User(**user_data.model_dump())
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def update_user(
    session: AsyncSession,
    user: User,
    user_data: UserUpdate,
) -> User:
    """
    Обновить данные пользователя.

    Args:
        session: Сессия БД
        user: Объект пользователя
        user_data: Данные для обновления

    Returns:
        Обновлённый пользователь
    """
    update_data = user_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    await session.commit()
    await session.refresh(user)
    return user


async def delete_user(session: AsyncSession, user: User) -> None:
    """
    Удалить пользователя.

    Args:
        session: Сессия БД
        user: Объект пользователя
    """
    await session.delete(user)
    await session.commit()


async def get_or_create_user(session: AsyncSession, user_data: UserCreate) -> tuple[User, bool]:
    """
    Получить существующего пользователя или создать нового.

    Args:
        session: Сессия БД
        user_data: Данные пользователя

    Returns:
        Кортеж (User, created: bool)
    """
    user = await get_user_by_telegram_id(session, user_data.telegram_id)
    if user:
        return user, False
    user = await create_user(session, user_data)
    return user, True
