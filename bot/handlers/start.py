"""
Обработчики команды /start и базовых действий.
"""

import asyncio

from api_client import api_client
from common import get_main_menu_keyboard_for_user
from keyboards import get_main_menu_keyboard
from loguru import logger
from telebot import TeleBot
from telebot.types import Message
from utils import safe_handler


def register_start_handlers(bot: TeleBot):
    """
    Регистрация обработчиков стартовых команд.

    Args:
        bot: Экземпляр TeleBot
    """
    safe = safe_handler(bot)

    @bot.message_handler(commands=["start"])
    @safe
    def cmd_start(message: Message):
        """Обработчик команды /start."""
        asyncio.run(_cmd_start_async(message))

    async def _cmd_start_async(message: Message):
        """Async реализация cmd_start."""
        logger.info(f"🚀 /start от @{message.from_user.username or message.from_user.id}")

        api_user = await api_client.get_or_create_user(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name or "Пользователь",
        )

        is_admin = bool(api_user.get("is_admin"))
        if not api_user.get("age") or not api_user.get("city"):
            bot.send_message(
                message.chat.id,
                f"👋 Привет, <b>{api_user['first_name']}</b>!\n\n"
                "Для начала работы заполните профиль.\nИспользуйте /register",
                reply_markup=get_main_menu_keyboard(is_admin=is_admin),
            )
        else:
            bot.send_message(
                message.chat.id,
                f"👋 Привет, <b>{api_user['first_name']}</b>!\n\n"
                "Я помогу найти компанию для совместных тренировок.\nВыбери действие:",
                reply_markup=get_main_menu_keyboard(is_admin=is_admin),
            )

    @bot.message_handler(commands=["help"])
    @safe
    def cmd_help(message: Message):
        """Обработчик команды /help."""
        logger.info(f"📖 /help от @{message.from_user.username or message.from_user.id}")
        keyboard = asyncio.run(get_main_menu_keyboard_for_user(api_client, message.from_user.id))
        bot.send_message(
            message.chat.id,
            "<b>📖 Помощь</b>\n\n"
            "🔹 <b>Мои тренировки</b> — список ваших тренировок\n"
            "🔹 <b>Мои рабочие веса</b> — добавление и просмотр веса\n"
            "🔹 <b>Найти тренировку</b> — поиск доступных тренировок\n"
            "🔹 <b>Создать тренировку</b> — создать новую тренировку\n"
            "🔹 <b>Профиль</b> — информация о вас\n\n"
            "<b>Команды:</b>\n"
            "/start — главное меню\n"
            "/register — регистрация профиля\n"
            "/applications — заявки на тренировки\n"
            "/cancel — отменить процесс\n"
            "/help — эта справка",
            reply_markup=keyboard,
        )
