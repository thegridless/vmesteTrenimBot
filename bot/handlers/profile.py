"""
Обработчики профиля пользователя.
"""

from loguru import logger
from telebot import TeleBot
from telebot.types import Message

from api_client import api_client
from keyboards import get_main_menu_keyboard
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
        user_tg = message.from_user
        logger.info(f"👤 Команда 'Профиль' от @{user_tg.username} (id={user_tg.id})")

        user = api_client.get_user_by_telegram_id(user_tg.id)
        if not user:
            bot.send_message(message.chat.id, "❌ Пользователь не найден. Используйте /start")
            return

        # Формируем текст профиля
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

        # Проверяем, заполнен ли профиль
        if not user.get("age") or not user.get("city"):
            text += "\n⚠️ Профиль не полностью заполнен. Используйте /register"

        bot.send_message(message.chat.id, text, reply_markup=get_main_menu_keyboard())
