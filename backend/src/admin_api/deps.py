"""
Зависимости для админских эндпоинтов.
"""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_session
from src.users.models import User
from src.users.repository import UserRepository

SessionDep = Annotated[AsyncSession, Depends(get_session)]


def get_user_repository(session: SessionDep) -> UserRepository:
    """
    Dependency для получения репозитория пользователей.

    Args:
        session: Асинхронная сессия БД

    Returns:
        Экземпляр UserRepository
    """
    return UserRepository(session)


UserRepoDep = Annotated[UserRepository, Depends(get_user_repository)]


async def get_admin_user(telegram_id: int, repo: UserRepoDep) -> User:
    """
    Dependency для проверки администратора по Telegram ID.

    Args:
        telegram_id: ID пользователя в Telegram
        repo: Репозиторий пользователей

    Returns:
        Экземпляр User
    """
    user = await repo.get_by_telegram_id(telegram_id)
    if not user or not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ запрещён",
        )
    return user


AdminUserDep = Annotated[User, Depends(get_admin_user)]
