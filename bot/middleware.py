"""
Middleware для логирования всех сообщений от пользователей.
"""

from loguru import logger
from telebot import TeleBot
from telebot.types import Message


def log_message_middleware(bot: TeleBot) -> None:
    """
    Middleware для логирования всех входящих сообщений.

    Args:
        bot: Экземпляр TeleBot
    """

    @bot.middleware_handler(update_types=["message"])
    def log_message(bot_instance: TeleBot, message: Message):  # noqa: ARG001
        """Логирование всех сообщений."""
        user = message.from_user
        if user:
            # Логируем команды отдельно
            if message.text and message.text.startswith("/"):
                logger.info(
                    f"📨 Команда '{message.text}' от @{user.username or 'N/A'} "
                    f"(id={user.id}, chat_id={message.chat.id})"
                )
            # Логируем текстовые сообщения
            elif message.text:
                # Проверяем состояние пользователя
                current_state = bot.get_state(user.id, message.chat.id)
                state_info = f", state={current_state}" if current_state else ", state=None"
                logger.debug(
                    f"💬 Сообщение от @{user.username or 'N/A'} "
                    f"(id={user.id}): {message.text[:50]}{state_info}"
                )
            # Логируем другие типы сообщений
            else:
                logger.debug(
                    f"📎 Медиа от @{user.username or 'N/A'} "
                    f"(id={user.id}, type={message.content_type})"
                )
