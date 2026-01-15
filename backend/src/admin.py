"""
Настройка FastAPI Admin панели.
"""

from sqladmin import Admin, ModelView
from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request

from src.config import settings
from src.database import engine
from src.events.models import Event, EventApplication, EventParticipant
from src.sports.models import Sport
from src.users.models import User


class AdminAuth(AuthenticationBackend):
    """
    Простая аутентификация для админ-панели.
    Использует переменные окружения для логина и пароля.
    """

    async def login(self, request: Request) -> bool:
        """
        Обработка входа в админ-панель.

        Args:
            request: HTTP запрос с данными формы

        Returns:
            True если авторизация успешна
        """
        form = await request.form()
        username = form.get("username")
        password = form.get("password")

        # Проверяем через переменные окружения
        from src.config import settings

        if username == settings.admin_username and password == settings.admin_password:
            request.session.update({"admin_authenticated": True})
            return True
        return False

    async def logout(self, request: Request) -> bool:
        """
        Выход из админ-панели.

        Args:
            request: HTTP запрос

        Returns:
            True
        """
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        """
        Проверка аутентификации для защищённых страниц.

        Args:
            request: HTTP запрос

        Returns:
            True если пользователь авторизован
        """
        return request.session.get("admin_authenticated", False)


authentication_backend = AdminAuth(secret_key=settings.admin_secret_key)


class UserAdmin(ModelView, model=User):
    """
    Админ-панель для управления пользователями.
    """

    name = "Пользователь"
    name_plural = "Пользователи"
    icon = "fa-solid fa-user"

    column_list = [User.id, User.telegram_id, User.username, User.first_name, User.created_at]
    column_searchable_list = [User.telegram_id, User.username, User.first_name]
    column_sortable_list = [User.id, User.telegram_id, User.created_at]
    column_details_list = [
        User.id,
        User.telegram_id,
        User.username,
        User.first_name,
        User.created_at,
    ]

    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True

    # Отображаем связанные данные
    column_labels = {
        User.id: "ID",
        User.telegram_id: "Telegram ID",
        User.username: "Username",
        User.first_name: "Имя",
        User.created_at: "Дата регистрации",
    }


class EventAdmin(ModelView, model=Event):
    """
    Админ-панель для управления мероприятиями.
    """

    name = "Мероприятие"
    name_plural = "Мероприятия"
    icon = "fa-solid fa-calendar"

    column_list = [
        Event.id,
        Event.title,
        Event.date,
        Event.location,
        Event.creator_id,
        Event.created_at,
    ]
    column_searchable_list = [Event.title, Event.description, Event.location]
    column_sortable_list = [Event.id, Event.date, Event.created_at]
    column_details_list = [
        Event.id,
        Event.title,
        Event.description,
        Event.date,
        Event.location,
        Event.creator_id,
        Event.created_at,
    ]

    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True

    # Отображаем связанные данные
    column_labels = {
        Event.id: "ID",
        Event.title: "Название",
        Event.description: "Описание",
        Event.date: "Дата и время",
        Event.location: "Место",
        Event.creator_id: "ID создателя",
        Event.created_at: "Дата создания",
    }


class EventParticipantAdmin(ModelView, model=EventParticipant):
    """
    Админ-панель для управления участниками мероприятий.
    """

    name = "Участник"
    name_plural = "Участники"
    icon = "fa-solid fa-users"

    column_list = [
        EventParticipant.id,
        EventParticipant.user_id,
        EventParticipant.event_id,
        EventParticipant.joined_at,
    ]
    column_searchable_list = [EventParticipant.user_id, EventParticipant.event_id]
    column_sortable_list = [EventParticipant.id, EventParticipant.joined_at]
    column_details_list = [
        EventParticipant.id,
        EventParticipant.user_id,
        EventParticipant.event_id,
        EventParticipant.joined_at,
    ]

    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True

    # Отображаем связанные данные
    column_labels = {
        EventParticipant.id: "ID",
        EventParticipant.user_id: "ID пользователя",
        EventParticipant.event_id: "ID мероприятия",
        EventParticipant.joined_at: "Дата присоединения",
    }


class SportAdmin(ModelView, model=Sport):
    """
    Админ-панель для управления видами спорта.
    """

    name = "Вид спорта"
    name_plural = "Виды спорта"
    icon = "fa-solid fa-dumbbell"

    column_list = [Sport.id, Sport.name, Sport.active]
    column_searchable_list = [Sport.name]
    column_sortable_list = [Sport.id, Sport.name, Sport.active]
    column_details_list = [Sport.id, Sport.name, Sport.active]

    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True

    column_labels = {
        Sport.id: "ID",
        Sport.name: "Название",
        Sport.active: "Активен",
    }


def setup_admin(app) -> Admin:
    """
    Настройка и создание админ-панели.

    Args:
        app: Экземпляр FastAPI приложения

    Returns:
        Экземпляр Admin
    """
    admin = Admin(
        app,
        engine,
        authentication_backend=authentication_backend,
        title="VmesteTrenim Admin",
        base_url="/admin",
    )

    # Регистрируем модели
    admin.add_view(UserAdmin)
    admin.add_view(SportAdmin)
    admin.add_view(EventAdmin)
    admin.add_view(EventParticipantAdmin)

    # Добавляем админку для заявок
    class EventApplicationAdmin(ModelView, model=EventApplication):
        """Админ-панель для заявок на участие."""

        name = "Заявка"
        name_plural = "Заявки"
        icon = "fa-solid fa-file-circle-check"

        column_list = [
            EventApplication.id,
            EventApplication.user_id,
            EventApplication.event_id,
            EventApplication.status,
            EventApplication.applied_at,
        ]
        column_searchable_list = [EventApplication.user_id, EventApplication.event_id]
        column_sortable_list = [EventApplication.id, EventApplication.applied_at]
        column_details_list = [
            EventApplication.id,
            EventApplication.user_id,
            EventApplication.event_id,
            EventApplication.status,
            EventApplication.applied_at,
            EventApplication.reviewed_at,
        ]

        can_create = True
        can_edit = True
        can_delete = True
        can_view_details = True

        column_labels = {
            EventApplication.id: "ID",
            EventApplication.user_id: "ID пользователя",
            EventApplication.event_id: "ID мероприятия",
            EventApplication.status: "Статус",
            EventApplication.applied_at: "Дата подачи",
            EventApplication.reviewed_at: "Дата рассмотрения",
        }

    admin.add_view(EventApplicationAdmin)

    return admin
