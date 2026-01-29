"""
API роутер для рассылок (доступен только администратору).
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.admin_api.deps import AdminUserDep
from src.broadcasts.repository import BroadcastRepository
from src.broadcasts.schemas import BroadcastComplete, BroadcastCreate, BroadcastResponse
from src.database import get_session

router = APIRouter(prefix="/admin/broadcasts", tags=["admin"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


def get_broadcast_repository(session: SessionDep) -> BroadcastRepository:
    """
    Dependency для получения репозитория рассылок.

    Args:
        session: Асинхронная сессия БД

    Returns:
        Экземпляр BroadcastRepository
    """
    return BroadcastRepository(session)


BroadcastRepoDep = Annotated[BroadcastRepository, Depends(get_broadcast_repository)]


@router.post("/", response_model=BroadcastResponse, status_code=status.HTTP_201_CREATED)
async def create_broadcast(
    data: BroadcastCreate,
    admin_user: AdminUserDep,
    repo: BroadcastRepoDep,
):
    """
    Создать рассылку.

    Args:
        data: Данные рассылки
        admin_user: Администратор
        repo: Репозиторий рассылок

    Returns:
        Созданная рассылка
    """
    return await repo.create_broadcast(admin_user.id, data.text)


@router.patch("/{broadcast_id}/complete", response_model=BroadcastResponse)
async def complete_broadcast(
    broadcast_id: int,
    data: BroadcastComplete,
    admin_user: AdminUserDep,  # noqa: ARG001
    repo: BroadcastRepoDep,
):
    """
    Завершить рассылку и сохранить статистику.

    Args:
        broadcast_id: ID рассылки
        data: Статистика рассылки
        admin_user: Администратор
        repo: Репозиторий рассылок

    Returns:
        Обновлённая рассылка
    """
    broadcast = await repo.get(broadcast_id)
    if not broadcast:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Рассылка не найдена",
        )
    return await repo.complete_broadcast(
        broadcast,
        total_count=data.total_count,
        success_count=data.success_count,
        fail_count=data.fail_count,
    )
