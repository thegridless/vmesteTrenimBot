"""
API роутер для пользователей.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_session
from src.users.repository import UserRepository
from src.users.schemas import UserCreate, UserResponse, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])

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


@router.get("/", response_model=list[UserResponse])
async def get_users(
    repo: UserRepoDep,
    skip: int = 0,
    limit: int = 100,
):
    """Получить список пользователей."""
    return await repo.list_users(skip=skip, limit=limit)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, repo: UserRepoDep):
    """Получить пользователя по ID."""
    user = await repo.get_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден",
        )
    return user


@router.get("/telegram/{telegram_id}", response_model=UserResponse)
async def get_user_by_telegram_id(telegram_id: int, repo: UserRepoDep):
    """Получить пользователя по Telegram ID."""
    user = await repo.get_by_telegram_id(telegram_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден",
        )
    return user


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user_data: UserCreate, repo: UserRepoDep):
    """Создать нового пользователя."""
    existing = await repo.get_by_telegram_id(user_data.telegram_id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким Telegram ID уже существует",
        )
    return await repo.create_user(user_data)


@router.post("/get-or-create", response_model=UserResponse)
async def get_or_create_user(user_data: UserCreate, repo: UserRepoDep):
    """Получить существующего пользователя или создать нового."""
    user, _ = await repo.get_or_create_user(user_data)
    return user


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(user_id: int, user_data: UserUpdate, repo: UserRepoDep):
    """Обновить данные пользователя."""
    user = await repo.get_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден",
        )
    return await repo.update_user(user, user_data)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int, repo: UserRepoDep):
    """Удалить пользователя."""
    user = await repo.get_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден",
        )
    await repo.delete_user(user)
