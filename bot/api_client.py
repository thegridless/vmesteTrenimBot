"""
HTTP клиент для взаимодействия с Backend API.
"""

from typing import Any

import httpx
from loguru import logger

from config import settings


class APIClient:
    """Асинхронный клиент для работы с Backend API."""

    def __init__(self):
        self.base_url = settings.api_base_url
        self.client = httpx.AsyncClient(timeout=30.0, follow_redirects=True)

    async def _request(
        self,
        method: str,
        endpoint: str,
        **kwargs,
    ) -> dict[str, Any] | list | None:
        """
        Выполнить HTTP запрос к API.

        Args:
            method: HTTP метод (GET, POST, PATCH, DELETE)
            endpoint: Путь эндпоинта
            **kwargs: Дополнительные параметры для httpx

        Returns:
            JSON ответ или None

        Raises:
            httpx.RequestError: Ошибка подключения
            httpx.HTTPStatusError: HTTP ошибка
        """
        url = f"{self.base_url}{endpoint}"

        try:
            response = await self.client.request(method, url, **kwargs)
            response.raise_for_status()

            if response.status_code == 204:
                return None
            return response.json()
        except httpx.ConnectError as e:
            logger.error(f"Ошибка подключения к API {url}: {e}")
            raise
        except httpx.TimeoutException as e:
            logger.error(f"Таймаут при запросе к API {url}: {e}")
            raise
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP ошибка {e.response.status_code} для {url}: {e.response.text}")
            raise

    # --- Users ---

    async def get_or_create_user(
        self,
        telegram_id: int,
        username: str | None,
        first_name: str,
        age: int | None = None,
        gender: str | None = None,
        city: str | None = None,
        sports: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Получить или создать пользователя.

        Args:
            telegram_id: ID пользователя в Telegram
            username: Username
            first_name: Имя
            age: Возраст
            gender: Пол
            city: Город
            sports: Виды спорта

        Returns:
            Данные пользователя
        """
        return await self._request(
            "POST",
            "/users/get-or-create",
            json={
                "telegram_id": telegram_id,
                "username": username,
                "first_name": first_name,
                "age": age,
                "gender": gender,
                "city": city,
                "sports": sports,
            },
        )

    async def get_user_by_telegram_id(self, telegram_id: int) -> dict[str, Any] | None:
        """
        Получить пользователя по Telegram ID.

        Args:
            telegram_id: ID пользователя в Telegram

        Returns:
            Данные пользователя или None
        """
        try:
            return await self._request("GET", f"/users/telegram/{telegram_id}")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise

    async def get_user_by_id(self, user_id: int) -> dict[str, Any] | None:
        """
        Получить пользователя по ID из БД.

        Args:
            user_id: ID пользователя в БД

        Returns:
            Данные пользователя или None
        """
        try:
            return await self._request("GET", f"/users/{user_id}")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise

    async def update_user(self, user_id: int, **kwargs) -> dict[str, Any]:
        """
        Обновить данные пользователя.

        Args:
            user_id: ID пользователя
            **kwargs: Поля для обновления

        Returns:
            Обновлённые данные пользователя
        """
        return await self._request("PATCH", f"/users/{user_id}", json=kwargs)

    # --- Events ---

    async def get_events(
        self,
        skip: int = 0,
        limit: int = 10,
        creator_id: int | None = None,
        sport_type: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Получить список мероприятий.

        Args:
            skip: Сколько пропустить
            limit: Максимум записей
            creator_id: Фильтр по создателю
            sport_type: Фильтр по виду спорта
            date_from: Фильтр по дате от (ISO)
            date_to: Фильтр по дате до (ISO)

        Returns:
            Список мероприятий
        """
        params = {"skip": skip, "limit": limit}
        if creator_id:
            params["creator_id"] = creator_id
        if sport_type:
            params["sport_type"] = sport_type
        if date_from:
            params["date_from"] = date_from
        if date_to:
            params["date_to"] = date_to
        return await self._request("GET", "/events", params=params)

    async def search_events(
        self,
        sport_type: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        skip: int = 0,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """
        Поиск мероприятий.

        Args:
            sport_type: Вид спорта
            date_from: Дата от (ISO)
            date_to: Дата до (ISO)
            skip: Сколько пропустить
            limit: Максимум записей

        Returns:
            Список мероприятий
        """
        return await self._request(
            "POST",
            "/events/search",
            json={
                "sport_type": sport_type,
                "date_from": date_from,
                "date_to": date_to,
                "skip": skip,
                "limit": limit,
            },
        )

    async def get_event(self, event_id: int) -> dict[str, Any] | None:
        """
        Получить мероприятие по ID.

        Args:
            event_id: ID мероприятия

        Returns:
            Данные мероприятия или None
        """
        try:
            return await self._request("GET", f"/events/{event_id}")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise

    async def create_event(
        self,
        title: str,
        date: str,
        creator_id: int,
        description: str | None = None,
        location: str | None = None,
        latitude: float | None = None,
        longitude: float | None = None,
        sport_type: str | None = None,
        max_participants: int | None = None,
        fee: float | None = None,
        note: str | None = None,
    ) -> dict[str, Any]:
        """
        Создать мероприятие.

        Args:
            title: Название
            date: Дата и время (ISO формат)
            creator_id: ID создателя
            description: Описание
            location: Место
            latitude: Широта
            longitude: Долгота
            sport_type: Вид спорта
            max_participants: Максимум участников
            fee: Взнос
            note: Примечание

        Returns:
            Созданное мероприятие
        """
        return await self._request(
            "POST",
            "/events",
            json={
                "title": title,
                "date": date,
                "creator_id": creator_id,
                "description": description,
                "location": location,
                "latitude": latitude,
                "longitude": longitude,
                "sport_type": sport_type,
                "max_participants": max_participants,
                "fee": fee,
                "note": note,
            },
        )

    async def delete_event(self, event_id: int) -> bool:
        """
        Удалить мероприятие.

        Args:
            event_id: ID мероприятия

        Returns:
            True если удалено
        """
        try:
            await self._request("DELETE", f"/events/{event_id}")
            return True
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return False
            raise

    # --- Participants ---

    async def join_event(self, event_id: int, user_id: int) -> dict[str, Any] | None:
        """
        Присоединиться к мероприятию.

        Args:
            event_id: ID мероприятия
            user_id: ID пользователя

        Returns:
            Данные участия или None если уже участвует
        """
        try:
            return await self._request(
                "POST",
                f"/events/{event_id}/participants/{user_id}",
            )
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 400:
                return None
            raise

    async def leave_event(self, event_id: int, user_id: int) -> bool:
        """
        Покинуть мероприятие.

        Args:
            event_id: ID мероприятия
            user_id: ID пользователя

        Returns:
            True если покинул
        """
        try:
            await self._request("DELETE", f"/events/{event_id}/participants/{user_id}")
            return True
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return False
            raise

    async def get_user_events(self, user_id: int) -> list[dict[str, Any]]:
        """
        Получить мероприятия пользователя (где он участник).

        Args:
            user_id: ID пользователя

        Returns:
            Список мероприятий
        """
        return await self._request("GET", f"/events/user/{user_id}")

    async def get_created_events(self, creator_id: int) -> list[dict[str, Any]]:
        """
        Получить созданные пользователем мероприятия.

        Args:
            creator_id: ID создателя

        Returns:
            Список мероприятий
        """
        return await self.get_events(creator_id=creator_id, limit=100)

    # --- Заявки на участие ---

    async def apply_to_event(self, event_id: int, user_id: int) -> dict[str, Any] | None:
        """
        Подать заявку на участие в мероприятии.

        Args:
            event_id: ID мероприятия
            user_id: ID пользователя

        Returns:
            Данные заявки или None если ошибка
        """
        try:
            return await self._request("POST", f"/events/{event_id}/apply", params={"user_id": user_id})
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 400:
                return None
            raise

    async def get_event_applications(
        self, event_id: int, status: str | None = None
    ) -> list[dict[str, Any]]:
        """
        Получить заявки на мероприятие.

        Args:
            event_id: ID мероприятия
            status: Фильтр по статусу (pending, approved, rejected)

        Returns:
            Список заявок
        """
        params = {}
        if status:
            params["status"] = status
        return await self._request("GET", f"/events/{event_id}/applications", params=params)

    async def get_user_applications(
        self, user_id: int, status: str | None = None
    ) -> list[dict[str, Any]]:
        """
        Получить заявки пользователя.

        Args:
            user_id: ID пользователя
            status: Фильтр по статусу

        Returns:
            Список заявок
        """
        params = {}
        if status:
            params["status"] = status
        return await self._request("GET", f"/events/applications/user/{user_id}", params=params)

    async def review_application(self, application_id: int, status: str) -> dict[str, Any]:
        """
        Рассмотреть заявку (подтвердить/отклонить).

        Args:
            application_id: ID заявки
            status: Статус (approved или rejected)

        Returns:
            Обновлённая заявка
        """
        return await self._request(
            "PATCH", f"/events/applications/{application_id}", json={"status": status}
        )

    async def close(self):
        """Закрыть соединение."""
        await self.client.aclose()


# Глобальный экземпляр клиента
api_client = APIClient()
