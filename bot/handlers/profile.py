"""
Обработчики профиля пользователя.
"""

import asyncio

from api_client import api_client
from keyboards import get_main_menu_keyboard
from loguru import logger
from telebot import TeleBot
from telebot.types import Message
from utils import safe_handler


def register_profile_handlers(bot: TeleBot):
    """
    Регистрация обработчиков профиля.

    Args:
        bot: Экземпляр TeleBot
    """
    safe = safe_handler(bot)

    @bot.message_handler(func=lambda m: m.text == "👤 Профиль")
    @safe
    def profile(message: Message):
        """Показать и редактировать профиль."""
        asyncio.run(_profile_async(message))

    async def _profile_async(message: Message):
        """Async реализация profile."""
        logger.info(f"👤 Профиль от @{message.from_user.username or message.from_user.id}")

        user = await api_client.get_user_by_telegram_id(message.from_user.id)
        if not user:
            bot.send_message(message.chat.id, "❌ Пользователь не найден. Используйте /start")
            return

        text = "<b>👤 Ваш профиль</b>\n\n"
        text += f"📛 Имя: {user['first_name']}\n"
        if user.get("username"):
            text += f"🔗 Username: @{user['username']}\n"
        if user.get("age"):
            text += f"🎂 Возраст: {user['age']} лет\n"
        if user.get("gender"):
            gender_map = {"male": "Мужской", "female": "Женский"}
            text += f"⚧️ Пол: {gender_map.get(user['gender'], user['gender'])}\n"
        if user.get("city"):
            text += f"📍 Город: {user['city']}\n"
        if user.get("sports"):
            text += f"🏋️ Виды спорта: {', '.join(user['sports'])}\n"
        if user.get("note"):
            text += f"📝 Примечание: {user['note']}\n"
        text += f"📅 Зарегистрирован: {user['created_at'][:10]}\n"

        if not user.get("age") or not user.get("city"):
            text += "\n⚠️ Профиль не заполнен. Используйте /register"

        bot.send_message(
            message.chat.id,
            text,
            reply_markup=get_main_menu_keyboard(is_admin=bool(user.get("is_admin"))),
        )
