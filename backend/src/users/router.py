"""
API роутер для пользователей.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_session
from src.users import crud
from src.users.schemas import UserCreate, UserResponse, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


@router.get("/", response_model=list[UserResponse])
async def get_users(
    session: SessionDep,
    skip: int = 0,
    limit: int = 100,
):
    """Получить список пользователей."""
    return await crud.get_users(session, skip=skip, limit=limit)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, session: SessionDep):
    """Получить пользователя по ID."""
    user = await crud.get_user_by_id(session, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден",
        )
    return user


@router.get("/telegram/{telegram_id}", response_model=UserResponse)
async def get_user_by_telegram_id(telegram_id: int, session: SessionDep):
    """Получить пользователя по Telegram ID."""
    user = await crud.get_user_by_telegram_id(session, telegram_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден",
        )
    return user


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user_data: UserCreate, session: SessionDep):
    """Создать нового пользователя."""
    existing = await crud.get_user_by_telegram_id(session, user_data.telegram_id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким Telegram ID уже существует",
        )
    return await crud.create_user(session, user_data)


@router.post("/get-or-create", response_model=UserResponse)
async def get_or_create_user(user_data: UserCreate, session: SessionDep):
    """Получить существующего пользователя или создать нового."""
    user, _ = await crud.get_or_create_user(session, user_data)
    return user


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(user_id: int, user_data: UserUpdate, session: SessionDep):
    """Обновить данные пользователя."""
    user = await crud.get_user_by_id(session, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден",
        )
    return await crud.update_user(session, user, user_data)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int, session: SessionDep):
    """Удалить пользователя."""
    user = await crud.get_user_by_id(session, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден",
        )
    await crud.delete_user(session, user)
