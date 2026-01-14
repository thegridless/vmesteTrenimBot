"""
Общие константы и вспомогательные функции для бота.
"""

from enum import StrEnum
from typing import Any

from loguru import logger
from telebot import TeleBot
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup


class SportType(StrEnum):
    """Виды спорта."""
    
    FOOTBALL = "Футбол"
    BASKETBALL = "Баскетбол"
    VOLLEYBALL = "Волейбол"
    TENNIS = "Теннис"
    RUNNING = "Бег"
    YOGA = "Йога"
    SWIMMING = "Плавание"
    CYCLING = "Велоспорт"
    GYM = "Тренажёрный зал"
    BOXING = "Бокс"


def get_sport_keyboard(callback_prefix: str = "sport_") -> InlineKeyboardMarkup:
    """
    Создать клавиатуру выбора видов спорта.
    
    Args:
        callback_prefix: Префикс для callback_data
        
    Returns:
        InlineKeyboardMarkup с кнопками видов спорта
    """
    keyboard = InlineKeyboardMarkup(row_width=2)
    for sport in SportType:
        keyboard.add(InlineKeyboardButton(sport.value, callback_data=f"{callback_prefix}{sport.value}"))
    return keyboard


async def get_user_or_error(
    api_client,
    bot: TeleBot,
    telegram_id: int,
    chat_id: int,
) -> dict[str, Any] | None:
    """
    Получить пользователя или отправить сообщение об ошибке.
    
    Args:
        api_client: Экземпляр APIClient
        bot: Экземпляр TeleBot
        telegram_id: ID пользователя в Telegram
        chat_id: ID чата
        
    Returns:
        Данные пользователя или None если не найден
    """
    try:
        user = await api_client.get_user_by_telegram_id(telegram_id)
        if not user:
            bot.send_message(chat_id, "❌ Пользователь не найден. Используйте /start")
            return None
        return user
    except Exception as e:
        logger.error(f"Ошибка получения пользователя {telegram_id}: {e}")
        bot.send_message(chat_id, "❌ Ошибка подключения к серверу")
        return None


def format_event_text(event: dict[str, Any], include_description: bool = False) -> str:
    """
    Форматировать текст информации о событии.
    
    Args:
        event: Данные события
        include_description: Включить описание события
        
    Returns:
        Отформатированный текст
    """
    text = f"🏋️ <b>{event['title']}</b>\n"
    text += f"📅 {event['date'][:16]}\n"
    
    if include_description and event.get("description"):
        text += f"📝 {event['description']}\n"
    
    if event.get("location"):
        text += f"📍 {event['location']}\n"
    
    if event.get("sport_type"):
        text += f"⚽ {event['sport_type']}\n"
    
    if event.get("max_participants"):
        text += f"👥 До {event['max_participants']} чел.\n"
    
    if event.get("fee"):
        text += f"💰 {event['fee']} руб.\n"
    
    return text


def format_user_info(user: dict[str, Any], include_username: bool = True) -> str:
    """
    Форматировать информацию о пользователе.
    
    Args:
        user: Данные пользователя
        include_username: Включить username
        
    Returns:
        Отформатированный текст
    """
    text = f"👤 {user['first_name']}"
    
    if include_username and user.get("username"):
        text += f" @{user['username']}"
    
    if user.get("age"):
        text += f", {user['age']} лет"
    
    if user.get("city"):
        text += f"\n📍 {user['city']}"
    
    return text


def format_application_text(event: dict[str, Any], applicant: dict[str, Any]) -> str:
    """
    Форматировать текст заявки на участие.
    
    Args:
        event: Данные события
        applicant: Данные заявителя
        
    Returns:
        Отформатированный текст заявки
    """
    text = "<b>📝 Заявка на тренировку:</b>\n"
    text += f"🏋️ <b>{event['title']}</b>\n\n"
    text += format_user_info(applicant, include_username=False)
    return text
