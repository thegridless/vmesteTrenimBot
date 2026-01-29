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

                error_text = (
                    "❌ Произошла ошибка. Попробуйте ещё раз.\n"
                    "Если ошибка повторяется — нажмите /cancel"
                )

                # Определяем тип обновления (Message или CallbackQuery)
                if isinstance(update, Message):
                    chat_id = update.chat.id
                    current_state = bot.get_state(update.from_user.id, chat_id)
                    logger.debug(
                        f"Состояние пользователя при ошибке: user_id={update.from_user.id}, chat_id={chat_id}, state={current_state}",
                    )
                    if settings.debug:
                        bot.send_message(chat_id, f"❌ Ошибка: {type(e).__name__}: {str(e)}")
                    else:
                        bot.send_message(chat_id, error_text)
                elif isinstance(update, CallbackQuery):
                    bot.answer_callback_query(update.id, "❌ Произошла ошибка")
                    current_state = bot.get_state(update.from_user.id, update.message.chat.id)
                    logger.debug(
                        f"Состояние пользователя при ошибке: user_id={update.from_user.id}, chat_id={update.message.chat.id}, state={current_state}",
                    )
                    if settings.debug:
                        bot.send_message(
                            update.message.chat.id, f"❌ Ошибка: {type(e).__name__}: {str(e)}"
                        )
                    else:
                        bot.send_message(update.message.chat.id, error_text)

        return wrapper

    return decorator


# Алиас для обратной совместимости
safe_callback = safe_handler


def check_state(
    bot: TeleBot,
    user_id: int,
    chat_id: int,
    expected_state: State,
    skip_commands: bool = True,
    message: Message | None = None,
) -> bool:
    """
    Проверка, находится ли пользователь в указанном состоянии.

    Args:
        bot: Экземпляр TeleBot
        user_id: ID пользователя
        chat_id: ID чата
        expected_state: Ожидаемое состояние
        skip_commands: Игнорировать команды (сообщения, начинающиеся с /)
        message: Объект сообщения (для проверки команд)

    Returns:
        True если состояние совпадает
    """
    if skip_commands and message and message.text and message.text.startswith("/"):
        return False
    current_state = bot.get_state(user_id, chat_id)
    return current_state == expected_state or str(current_state) == str(expected_state)


def create_state_checker(
    bot: TeleBot,
    expected_state: State,
    skip_commands: bool = True,
    allowed_content_types: set[str] | None = None,
):
    """
    Создать функцию-проверку состояния для message_handler.

    Args:
        bot: Экземпляр TeleBot
        expected_state: Ожидаемое состояние
        skip_commands: Игнорировать команды (сообщения, начинающиеся с /)
        allowed_content_types: Разрешенные типы сообщений (по умолчанию только text)

    Returns:
        Функция для проверки состояния
    """

    def checker(message: Message) -> bool:
        types = allowed_content_types or {"text"}
        if message.content_type not in types:
            return False
        return check_state(
            bot,
            message.from_user.id,
            message.chat.id,
            expected_state,
            skip_commands=skip_commands,
            message=message,
        )

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
