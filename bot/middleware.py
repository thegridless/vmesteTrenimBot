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
        if not user:
            return
        
        username = f"@{user.username}" if user.username else f"id{user.id}"
        
        # Логируем команды
        if message.text and message.text.startswith("/"):
            logger.info(f"📨 {message.text} от {username}")
        # Логируем медиа
        elif message.content_type != "text":
            logger.info(f"📎 {message.content_type} от {username}")
