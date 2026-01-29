"""
Клавиатуры для администрирования.
"""

from telebot.types import KeyboardButton, ReplyKeyboardMarkup


def get_admin_menu_keyboard() -> ReplyKeyboardMarkup:
    """
    Получить клавиатуру админ-меню.

    Returns:
        ReplyKeyboardMarkup с кнопками админ-меню
    """
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    keyboard.add(KeyboardButton("📣 Рассылка всем"))
    keyboard.add(KeyboardButton("✉️ Личное сообщение"))
    keyboard.add(KeyboardButton("⬅️ Назад"))
    return keyboard
