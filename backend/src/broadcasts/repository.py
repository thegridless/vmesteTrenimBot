"""
Репозиторий для работы с рассылками.
"""

from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from src.broadcasts.models import Broadcast
from src.repositories.base import BaseRepository


class BroadcastRepository(BaseRepository[Broadcast]):
    """
    Репозиторий для операций с рассылками.
    """

    def __init__(self, session: AsyncSession) -> None:
        """
        Инициализация репозитория рассылок.

        Args:
            session: Асинхронная сессия БД
        """
        super().__init__(session, Broadcast)

    async def create_broadcast(self, admin_user_id: int, text: str) -> Broadcast:
        """
        Создать рассылку.

        Args:
            admin_user_id: ID администратора
            text: Текст рассылки

        Returns:
            Созданная рассылка
        """
        broadcast = Broadcast(
            admin_user_id=admin_user_id,
            text=text,
            status="pending",
        )
        return await self.add(broadcast)

    async def complete_broadcast(
        self,
        broadcast: Broadcast,
        total_count: int,
        success_count: int,
        fail_count: int,
    ) -> Broadcast:
        """
        Завершить рассылку и сохранить статистику.

        Args:
            broadcast: Экземпляр рассылки
            total_count: Всего получателей
            success_count: Успешных отправок
            fail_count: Ошибок отправки

        Returns:
            Обновлённая рассылка
        """
        update_data = {
            "total_count": total_count,
            "success_count": success_count,
            "fail_count": fail_count,
            "status": "completed",
            "completed_at": datetime.now(UTC),
        }
        return await self.update(broadcast, update_data)
