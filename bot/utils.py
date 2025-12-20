"""
Утилиты для бота.
"""

import traceback
from collections.abc import Callable
from functools import wraps

from loguru import logger
from telebot import TeleBot
from telebot.handler_backends import State
from telebot.types import CallbackQuery, Message

from config import settings


def safe_handler(bot: TeleBot):
    """
    Декоратор для безопасной обработки ошибок в handlers.
    При DEBUG=True выводит ошибку в чат.

    Args:
        bot: Экземпляр TeleBot

    Usage:
        @safe_handler(bot)
        def my_handler(message: Message):
            # ваш код
    """

    def decorator(func: Callable):
        @wraps(func)
        def wrapper(message: Message, *args, **kwargs):
            # Логируем вызов обработчика для отладки
            if hasattr(message, "from_user") and message.from_user:
                logger.debug(
                    f"🔧 @safe wrapper вызван для {func.__name__} от "
                    f"@{message.from_user.username or 'N/A'} (id={message.from_user.id})"
                )
            try:
                return func(message, *args, **kwargs)
            except Exception as e:
                error_msg = f"❌ Ошибка: {type(e).__name__}: {str(e)}"

                if settings.debug:
                    # В режиме отладки показываем полную ошибку
                    full_error = f"{error_msg}\n\n<code>{traceback.format_exc()}</code>"
                    try:
                        bot.send_message(
                            message.chat.id,
                            full_error,
                            parse_mode="HTML",
                        )
                    except Exception:
                        # Если не удалось отправить (например, слишком длинное сообщение)
                        bot.send_message(
                            message.chat.id,
                            f"{error_msg}\n\nОшибка слишком длинная для отображения.",
                        )
                else:
                    # В продакшене показываем только общее сообщение
                    try:
                        bot.send_message(
                            message.chat.id,
                            "❌ Произошла ошибка. Попробуйте позже или используйте /cancel для отмены.",
                        )
                    except Exception:
                        pass  # Если не удалось отправить, просто логируем

                # Всегда логируем ошибку
                logger.error(
                    f"Ошибка в handler {func.__name__}: {e}",
                    exc_info=True,
                )
                return None

        return wrapper

    return decorator


def safe_callback(bot: TeleBot):
    """
    Декоратор для безопасной обработки ошибок в callback handlers.
    При DEBUG=True выводит ошибку в чат.

    Args:
        bot: Экземпляр TeleBot

    Usage:
        @safe_callback(bot)
        def my_callback(call):
            # ваш код
    """

    def decorator(func: Callable):
        @wraps(func)
        def wrapper(call, *args, **kwargs):
            # Логируем вызов callback обработчика для отладки
            if hasattr(call, "from_user") and call.from_user:
                logger.debug(
                    f"🔧 @safe_callback wrapper вызван для {func.__name__} от "
                    f"@{call.from_user.username or 'N/A'} (id={call.from_user.id}), "
                    f"data={call.data}"
                )
            try:
                return func(call, *args, **kwargs)
            except Exception as e:
                error_msg = f"❌ Ошибка: {type(e).__name__}: {str(e)}"

                if settings.debug:
                    # В режиме отладки показываем полную ошибку
                    full_error = f"{error_msg}\n\n<code>{traceback.format_exc()}</code>"
                    try:
                        bot.send_message(
                            call.message.chat.id,
                            full_error,
                            parse_mode="HTML",
                        )
                        bot.answer_callback_query(call.id, "❌ Ошибка (см. сообщение)")
                    except Exception:
                        bot.answer_callback_query(call.id, error_msg)
                else:
                    # В продакшене показываем только общее сообщение
                    try:
                        bot.answer_callback_query(call.id, "❌ Произошла ошибка")
                    except Exception:
                        pass

                # Всегда логируем ошибку
                logger.error(
                    f"Ошибка в callback handler {func.__name__}: {e}",
                    exc_info=True,
                )
                return None

        return wrapper

    return decorator


def check_state(
    bot: TeleBot, user_id: int, chat_id: int, expected_state: State, skip_commands: bool = True
) -> bool:
    """
    Проверка, находится ли пользователь в указанном состоянии.

    Args:
        bot: Экземпляр TeleBot
        user_id: ID пользователя
        chat_id: ID чата
        expected_state: Ожидаемое состояние (объект State)
        skip_commands: Пропускать команды (по умолчанию True)

    Returns:
        True если состояние совпадает, False иначе
    """
    current_state = bot.get_state(user_id, chat_id)

    # Сравниваем состояния (get_state возвращает строку, а не объект State)
    current_str = str(current_state) if current_state else ""
    expected_str = str(expected_state)

    # Убираем угловые скобки для сравнения
    current_clean = current_str.replace("<", "").replace(">", "")
    expected_clean = expected_str.replace("<", "").replace(">", "")

    # Проверяем совпадение разными способами
    match = (
        current_state == expected_state
        or current_str == expected_str
        or current_clean == expected_clean
        or (current_state and expected_state.name in str(current_state))
    )

    logger.debug(
        f"🔍 Проверка состояния: user_id={user_id}, "
        f"current={current_state}, expected={expected_state}, match={match}"
    )

    return match


def create_state_checker(bot: TeleBot, expected_state: State, skip_commands: bool = True):
    """
    Создает функцию-проверку состояния для использования в message_handler(func=...).

    Args:
        bot: Экземпляр TeleBot
        expected_state: Ожидаемое состояние
        skip_commands: Пропускать команды (по умолчанию True)

    Returns:
        Функция для проверки состояния сообщения
    """

    def checker(message: Message) -> bool:
        """Проверка состояния для message handler."""
        # Пропускаем команды, если нужно
        if skip_commands and message.text and message.text.startswith("/"):
            return False

        if message.content_type != "text":
            return False

        return check_state(
            bot, message.from_user.id, message.chat.id, expected_state, skip_commands
        )

    return checker


def create_callback_state_checker(
    bot: TeleBot, expected_state: State, data_prefix: str = None, allowed_data: list = None
):
    """
    Создает функцию-проверку состояния для использования в callback_query_handler(func=...).

    Args:
        bot: Экземпляр TeleBot
        expected_state: Ожидаемое состояние
        data_prefix: Префикс callback_data (опционально)
        allowed_data: Список разрешенных значений callback_data, которые не требуют префикса (опционально)

    Returns:
        Функция для проверки состояния callback
    """

    def checker(call: CallbackQuery) -> bool:
        """Проверка состояния для callback handler."""
        # Проверяем разрешенные значения без префикса (например, "sports_done")
        if allowed_data and call.data in allowed_data:
            return check_state(
                bot, call.from_user.id, call.message.chat.id, expected_state, skip_commands=False
            )

        # Проверяем префикс callback_data, если указан
        if data_prefix and (not call.data or not call.data.startswith(data_prefix)):
            return False

        return check_state(
            bot, call.from_user.id, call.message.chat.id, expected_state, skip_commands=False
        )

    return checker
