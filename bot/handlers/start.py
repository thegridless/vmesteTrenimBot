"""
Обработчики команды /start и базовых действий.
"""

from loguru import logger
from telebot import TeleBot
from telebot.types import Message

from api_client import api_client
from keyboards import get_main_menu_keyboard
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

            # Проверяем, заполнен ли профиль
            if not api_user.get("age") or not api_user.get("city"):
                bot.send_message(
                    message.chat.id,
                    f"👋 Привет, <b>{api_user['first_name']}</b>!\n\n"
                    "Для начала работы нужно заполнить профиль.\n"
                    "Используйте /register для регистрации.",
                    reply_markup=get_main_menu_keyboard(),
                )
            else:
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
    @safe
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
            "/register — регистрация/заполнение профиля\n"
            "/applications — заявки на мои тренировки\n"
            "/cancel — отменить текущий процесс\n"
            "/help — эта справка",
            reply_markup=get_main_menu_keyboard(),
        )
