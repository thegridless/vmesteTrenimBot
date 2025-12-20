"""
Обработчики команды /start и базовых действий.
"""

from loguru import logger
from telebot import TeleBot
from telebot.types import Message

from api_client import api_client
from keyboards import get_main_menu_keyboard


def register_start_handlers(bot: TeleBot):
    """
    Регистрация обработчиков стартовых команд.

    Args:
        bot: Экземпляр TeleBot
    """

    @bot.message_handler(commands=["start"])
    def cmd_start(message: Message):
        """Обработчик команды /start."""
        user = message.from_user
        logger.info(f"👤 /start от @{user.username} (id={user.id})")

        # Регистрируем или получаем пользователя
        try:
            api_user = api_client.get_or_create_user(
                telegram_id=user.id,
                username=user.username,
                first_name=user.first_name or "Пользователь",
            )
            logger.debug(f"Пользователь получен/создан: {api_user}")

            bot.send_message(
                message.chat.id,
                f"👋 Привет, <b>{api_user['first_name']}</b>!\n\n"
                "Я помогу найти компанию для совместных тренировок.\n"
                "Выбери действие:",
                reply_markup=get_main_menu_keyboard(),
            )
        except Exception as e:
            logger.error(f"Ошибка при регистрации пользователя {user.id}: {e}")
            bot.send_message(
                message.chat.id,
                "❌ Произошла ошибка при подключении к серверу. Попробуйте позже.",
            )

    @bot.message_handler(commands=["help"])
    def cmd_help(message: Message):
        """Обработчик команды /help."""
        user = message.from_user
        logger.info(f"👤 /help от @{user.username} (id={user.id})")
        bot.send_message(
            message.chat.id,
            "<b>📖 Помощь</b>\n\n"
            "🔹 <b>Мои тренировки</b> — список ваших тренировок\n"
            "🔹 <b>Найти тренировку</b> — поиск доступных тренировок\n"
            "🔹 <b>Создать тренировку</b> — создать новую тренировку\n"
            "🔹 <b>Профиль</b> — информация о вас\n\n"
            "Команды:\n"
            "/start — главное меню\n"
            "/help — эта справка",
            reply_markup=get_main_menu_keyboard(),
        )

    @bot.message_handler(func=lambda m: m.text == "📋 Мои тренировки")
    def my_events(message: Message):
        """Показать тренировки пользователя."""
        user = message.from_user
        logger.info(f"👤 Команда 'Мои тренировки' от @{user.username} (id={user.id})")
        user = api_client.get_user_by_telegram_id(message.from_user.id)
        if not user:
            bot.send_message(message.chat.id, "❌ Пользователь не найден. Используйте /start")
            return

        try:
            events = api_client.get_user_events(user["id"])
            if not events:
                bot.send_message(
                    message.chat.id,
                    "📭 У вас пока нет тренировок.\n"
                    "Создайте свою или присоединитесь к существующей!",
                    reply_markup=get_main_menu_keyboard(),
                )
                return

            text = "<b>📋 Ваши тренировки:</b>\n\n"
            for event in events[:10]:
                text += f"🏋️ <b>{event['title']}</b>\n"
                text += f"📅 {event['date']}\n"
                if event.get("location"):
                    text += f"📍 {event['location']}\n"
                text += "\n"

            bot.send_message(message.chat.id, text, reply_markup=get_main_menu_keyboard())
        except Exception as e:
            logger.error(f"Ошибка при загрузке тренировок: {e}")
            bot.send_message(message.chat.id, "❌ Ошибка при загрузке тренировок.")

    @bot.message_handler(func=lambda m: m.text == "🔍 Найти тренировку")
    def find_events(message: Message):
        """Показать доступные тренировки."""
        user = message.from_user
        logger.info(f"👤 Команда 'Найти тренировку' от @{user.username} (id={user.id})")
        try:
            events = api_client.get_events(limit=10)
            if not events:
                bot.send_message(
                    message.chat.id,
                    "📭 Пока нет доступных тренировок.",
                    reply_markup=get_main_menu_keyboard(),
                )
                return

            text = "<b>🔍 Доступные тренировки:</b>\n\n"
            for event in events:
                text += f"🏋️ <b>{event['title']}</b>\n"
                text += f"📅 {event['date']}\n"
                if event.get("location"):
                    text += f"📍 {event['location']}\n"
                text += "\n"

            bot.send_message(message.chat.id, text, reply_markup=get_main_menu_keyboard())
        except Exception as e:
            logger.error(f"Ошибка при поиске тренировок: {e}")
            bot.send_message(message.chat.id, "❌ Ошибка при загрузке тренировок.")

    @bot.message_handler(func=lambda m: m.text == "👤 Профиль")
    def profile(message: Message):
        """Показать профиль пользователя."""
        user_tg = message.from_user
        logger.info(f"👤 Команда 'Профиль' от @{user_tg.username} (id={user_tg.id})")
        user = api_client.get_user_by_telegram_id(user_tg.id)
        if not user:
            bot.send_message(message.chat.id, "❌ Пользователь не найден. Используйте /start")
            return

        text = "<b>👤 Ваш профиль</b>\n\n"
        text += f"📛 Имя: {user['first_name']}\n"
        if user.get("username"):
            text += f"🔗 Username: @{user['username']}\n"
        text += f"📅 Зарегистрирован: {user['created_at'][:10]}\n"

        bot.send_message(message.chat.id, text, reply_markup=get_main_menu_keyboard())

    @bot.message_handler(func=lambda m: m.text == "➕ Создать тренировку")
    def create_event_start(message: Message):
        """Начать создание тренировки (заглушка)."""
        user = message.from_user
        logger.info(f"👤 Команда 'Создать тренировку' от @{user.username} (id={user.id})")
        bot.send_message(
            message.chat.id,
            "🚧 Функция создания тренировок в разработке.\n" "Скоро будет доступна!",
            reply_markup=get_main_menu_keyboard(),
        )
