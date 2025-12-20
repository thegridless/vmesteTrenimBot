"""
HTTP клиент для взаимодействия с Backend API.
"""

from typing import Any

import httpx
from loguru import logger

from config import settings


class APIClient:
    """Клиент для работы с Backend API."""

    def __init__(self):
        self.base_url = settings.api_base_url
        self.client = httpx.Client(timeout=30.0, follow_redirects=True)

    def _request(
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
        logger.debug(f"API запрос: {method} {url}")

        try:
            response = self.client.request(method, url, **kwargs)
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

    def get_or_create_user(
        self,
        telegram_id: int,
        username: str | None,
        first_name: str,
    ) -> dict[str, Any]:
        """
        Получить или создать пользователя.

        Args:
            telegram_id: ID пользователя в Telegram
            username: Username
            first_name: Имя

        Returns:
            Данные пользователя
        """
        return self._request(
            "POST",
            "/users/get-or-create",
            json={
                "telegram_id": telegram_id,
                "username": username,
                "first_name": first_name,
            },
        )

    def get_user_by_telegram_id(self, telegram_id: int) -> dict[str, Any] | None:
        """
        Получить пользователя по Telegram ID.

        Args:
            telegram_id: ID пользователя в Telegram

        Returns:
            Данные пользователя или None
        """
        try:
            return self._request("GET", f"/users/telegram/{telegram_id}")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise

    # --- Events ---

    def get_events(
        self,
        skip: int = 0,
        limit: int = 10,
        creator_id: int | None = None,
    ) -> list[dict[str, Any]]:
        """
        Получить список мероприятий.

        Args:
            skip: Сколько пропустить
            limit: Максимум записей
            creator_id: Фильтр по создателю

        Returns:
            Список мероприятий
        """
        params = {"skip": skip, "limit": limit}
        if creator_id:
            params["creator_id"] = creator_id
        return self._request("GET", "/events", params=params)

    def get_event(self, event_id: int) -> dict[str, Any] | None:
        """
        Получить мероприятие по ID.

        Args:
            event_id: ID мероприятия

        Returns:
            Данные мероприятия или None
        """
        try:
            return self._request("GET", f"/events/{event_id}")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise

    def create_event(
        self,
        title: str,
        date: str,
        creator_id: int,
        description: str | None = None,
        location: str | None = None,
    ) -> dict[str, Any]:
        """
        Создать мероприятие.

        Args:
            title: Название
            date: Дата и время (ISO формат)
            creator_id: ID создателя
            description: Описание
            location: Место

        Returns:
            Созданное мероприятие
        """
        return self._request(
            "POST",
            "/events",
            json={
                "title": title,
                "date": date,
                "creator_id": creator_id,
                "description": description,
                "location": location,
            },
        )

    def delete_event(self, event_id: int) -> bool:
        """
        Удалить мероприятие.

        Args:
            event_id: ID мероприятия

        Returns:
            True если удалено
        """
        try:
            self._request("DELETE", f"/events/{event_id}")
            return True
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return False
            raise

    # --- Participants ---

    def join_event(self, event_id: int, user_id: int) -> dict[str, Any] | None:
        """
        Присоединиться к мероприятию.

        Args:
            event_id: ID мероприятия
            user_id: ID пользователя

        Returns:
            Данные участия или None если уже участвует
        """
        try:
            return self._request(
                "POST",
                f"/events/{event_id}/participants/{user_id}",
            )
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 400:
                return None
            raise

    def leave_event(self, event_id: int, user_id: int) -> bool:
        """
        Покинуть мероприятие.

        Args:
            event_id: ID мероприятия
            user_id: ID пользователя

        Returns:
            True если покинул
        """
        try:
            self._request("DELETE", f"/events/{event_id}/participants/{user_id}")
            return True
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return False
            raise

    def get_user_events(self, user_id: int) -> list[dict[str, Any]]:
        """
        Получить мероприятия пользователя.

        Args:
            user_id: ID пользователя

        Returns:
            Список мероприятий
        """
        return self._request("GET", f"/events/user/{user_id}")

    def close(self):
        """Закрыть соединение."""
        self.client.close()


# Глобальный экземпляр клиента
api_client = APIClient()
