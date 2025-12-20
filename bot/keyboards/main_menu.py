"""
Клавиатуры для главного меню бота.
"""

from telebot.types import KeyboardButton, ReplyKeyboardMarkup


def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    """
    Получить клавиатуру главного меню.

    Returns:
        ReplyKeyboardMarkup с кнопками меню
    """
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    keyboard.add(
        KeyboardButton("📋 Мои тренировки"),
        KeyboardButton("🔍 Найти тренировку"),
    )
    keyboard.add(
        KeyboardButton("➕ Создать тренировку"),
        KeyboardButton("👤 Профиль"),
    )
    return keyboard
