"""
Утилиты для бота.
"""

from collections.abc import Callable
from functools import wraps

from config import settings
from loguru import logger
from telebot import TeleBot
from telebot.handler_backends import State
from telebot.types import CallbackQuery, Message


def safe_handler(bot: TeleBot):
    """
    Декоратор для безопасной обработки ошибок в обработчиках.

    Args:
        bot: Экземпляр TeleBot
    """

    def decorator(func: Callable):
        @wraps(func)
        def wrapper(update, *args, **kwargs):
            try:
                return func(update, *args, **kwargs)
            except Exception as e:
                logger.error(f"Ошибка в {func.__name__}: {e}", exc_info=settings.debug)
                
                # Определяем тип обновления (Message или CallbackQuery)
                if isinstance(update, Message):
                    chat_id = update.chat.id
                    if settings.debug:
                        bot.send_message(chat_id, f"❌ Ошибка: {type(e).__name__}: {str(e)}")
                    else:
                        bot.send_message(chat_id, "❌ Произошла ошибка. Попробуйте позже.")
                elif isinstance(update, CallbackQuery):
                    bot.answer_callback_query(update.id, "❌ Произошла ошибка")
                    if settings.debug:
                        bot.send_message(update.message.chat.id, f"❌ Ошибка: {type(e).__name__}: {str(e)}")

        return wrapper

    return decorator


# Алиас для обратной совместимости
safe_callback = safe_handler


def check_state(bot: TeleBot, user_id: int, chat_id: int, expected_state: State) -> bool:
    """
    Проверка, находится ли пользователь в указанном состоянии.

    Args:
        bot: Экземпляр TeleBot
        user_id: ID пользователя
        chat_id: ID чата
        expected_state: Ожидаемое состояние

    Returns:
        True если состояние совпадает
    """
    current_state = bot.get_state(user_id, chat_id)
    return current_state == expected_state or str(current_state) == str(expected_state)


def create_state_checker(bot: TeleBot, expected_state: State):
    """
    Создать функцию-проверку состояния для message_handler.

    Args:
        bot: Экземпляр TeleBot
        expected_state: Ожидаемое состояние

    Returns:
        Функция для проверки состояния
    """

    def checker(message: Message) -> bool:
        if message.text and message.text.startswith("/"):
            return False
        if message.content_type != "text":
            return False
        return check_state(bot, message.from_user.id, message.chat.id, expected_state)

    return checker


def create_callback_state_checker(
    bot: TeleBot, expected_state: State, data_prefix: str = None, allowed_data: list = None
):
    """
    Создать функцию-проверку состояния для callback_query_handler.

    Args:
        bot: Экземпляр TeleBot
        expected_state: Ожидаемое состояние
        data_prefix: Префикс callback_data
        allowed_data: Список разрешенных значений без префикса

    Returns:
        Функция для проверки состояния
    """

    def checker(call: CallbackQuery) -> bool:
        if allowed_data and call.data in allowed_data:
            return check_state(bot, call.from_user.id, call.message.chat.id, expected_state)
        if data_prefix and (not call.data or not call.data.startswith(data_prefix)):
            return False
        return check_state(bot, call.from_user.id, call.message.chat.id, expected_state)

    return checker
