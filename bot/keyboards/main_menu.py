"""
Клавиатуры для главного меню бота.
"""

from telebot.types import KeyboardButton, ReplyKeyboardMarkup


def get_main_menu_keyboard(is_admin: bool = False) -> ReplyKeyboardMarkup:
    """
    Получить клавиатуру главного меню.

    Returns:
        ReplyKeyboardMarkup с кнопками меню
    """
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    keyboard.add(
        KeyboardButton("📋 Мои тренировки"),
        KeyboardButton("⚖️ Мои рабочие веса"),
    )
    keyboard.add(
        KeyboardButton("🔍 Найти тренировку"),
        KeyboardButton("➕ Создать тренировку"),
    )
    keyboard.add(
        KeyboardButton("👤 Профиль"),
        KeyboardButton("📝 Заявки"),
    )
    if is_admin:
        keyboard.add(KeyboardButton("Администрирование"))
    return keyboard
