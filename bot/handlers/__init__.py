from handlers.start import register_start_handlers


def register_all_handlers(bot):
    """
    Регистрация всех обработчиков.

    Args:
        bot: Экземпляр TeleBot
    """
    register_start_handlers(bot)
