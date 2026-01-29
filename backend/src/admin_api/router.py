"""
Админские эндпоинты API.
"""

from fastapi import APIRouter

from src.admin_api.deps import AdminUserDep, UserRepoDep
from src.users.schemas import UserResponse

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users", response_model=list[UserResponse])
async def admin_list_users(
    admin_user: AdminUserDep,  # noqa: ARG001
    repo: UserRepoDep,
    skip: int = 0,
    limit: int = 100,
):
    """
    Получить список пользователей (только для администратора).

    Args:
        admin_user: Администратор
        repo: Репозиторий пользователей
        skip: Сколько записей пропустить
        limit: Максимальное количество записей

    Returns:
        Список пользователей
    """
    return await repo.list_users(skip=skip, limit=limit)
