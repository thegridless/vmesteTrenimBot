from handlers.admin import register_admin_handlers
from handlers.applications import register_applications_handlers
from handlers.events import register_events_handlers
from handlers.profile import register_profile_handlers
from handlers.registration import register_registration_handlers
from handlers.start import register_start_handlers
from handlers.unknown import register_unknown_handlers
from handlers.weights import register_weights_handlers


def register_all_handlers(bot):
    """
    Регистрация всех обработчиков.

    Args:
        bot: Экземпляр TeleBot
    """
    register_start_handlers(bot)
    register_registration_handlers(bot)
    register_profile_handlers(bot)
    register_events_handlers(bot)
    register_applications_handlers(bot)
    register_weights_handlers(bot)
    register_admin_handlers(bot)
    # Обработчик неизвестных команд должен быть последним
    register_unknown_handlers(bot)
