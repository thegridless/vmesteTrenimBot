"""
Обработчик неизвестных команд и сообщений.
"""

from loguru import logger
from telebot import TeleBot
from telebot.types import Message

from keyboards import get_main_menu_keyboard


def register_unknown_handlers(bot: TeleBot):
    """
    Регистрация обработчиков для неизвестных команд и сообщений.

    Args:
        bot: Экземпляр TeleBot
    """

    @bot.message_handler(commands=["cancel"])
    def cmd_cancel(message: Message):
        """Отменить текущий процесс (регистрация, создание события)."""
        user = message.from_user
        logger.info(f"👤 /cancel от @{user.username} (id={user.id})")
        logger.debug(f"🔧 cmd_cancel вызван для @{user.username} (id={user.id})")

        # Проверяем, есть ли активное состояние
        current_state = bot.get_state(user.id, message.chat.id)

        if current_state:
            bot.delete_state(user.id, message.chat.id)
            bot.send_message(
                message.chat.id,
                "❌ Процесс отменён.\n" "Используйте /start для возврата в главное меню.",
                reply_markup=get_main_menu_keyboard(),
            )
        else:
            bot.send_message(
                message.chat.id,
                "Нет активного процесса для отмены.",
                reply_markup=get_main_menu_keyboard(),
            )

    def check_no_state(message: Message) -> bool:
        """Проверка, что у пользователя нет активного состояния."""
        if message.content_type != "text":
            return False

        current_state = bot.get_state(message.from_user.id, message.chat.id)
        has_no_state = current_state is None

        # Логируем проверку для отладки
        logger.debug(
            f"🔍 Проверка состояния для handle_unknown_message: "
            f"user_id={message.from_user.id}, "
            f"current_state={current_state}, "
            f"has_no_state={has_no_state}"
        )

        return has_no_state

    @bot.message_handler(func=check_no_state)
    def handle_unknown_message(message: Message):
        """
        Обработчик всех неизвестных текстовых сообщений.
        Должен быть последним в цепочке обработчиков.

        ВАЖНО: Этот handler регистрируется ТОЛЬКО для текстовых сообщений БЕЗ активного FSM состояния.
        Используем func= для фильтрации на уровне декоратора, чтобы не перехватывать
        сообщения с активным состоянием (они обрабатываются стейт-обработчиками).
        """
        user = message.from_user

        # Дополнительная проверка на случай, если состояние изменилось между проверкой в func и вызовом функции
        current_state = bot.get_state(user.id, message.chat.id)
        if current_state:
            logger.warning(
                f"⚠️ handle_unknown_message вызван для сообщения со стейтом! "
                f"@{user.username} (id={user.id}): text='{message.text}', state={current_state}"
            )
            return  # Пропускаем, пусть обрабатывают стейт-обработчики

        logger.info(
            f"⚠️ handle_unknown_message вызван для @{user.username} (id={user.id}): "
            f"text='{message.text}', state={current_state}"
        )
        logger.debug(f"Неизвестное сообщение от @{user.username}: {message.text}")

        # Проверяем, не является ли это командой
        if message.text and message.text.startswith("/"):
            bot.send_message(
                message.chat.id,
                "❓ Неизвестная команда.\n\n"
                "Используйте /help для списка доступных команд или выберите действие из меню:",
                reply_markup=get_main_menu_keyboard(),
            )
        else:
            bot.send_message(
                message.chat.id,
                "❓ Не понимаю эту команду.\n\n"
                "Используйте /help для списка доступных команд или выберите действие из меню:",
                reply_markup=get_main_menu_keyboard(),
            )
