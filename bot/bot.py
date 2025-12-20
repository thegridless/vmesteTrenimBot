"""
Инициализация Telegram бота.
"""

import telebot

from config import settings

# Создаём экземпляр бота
bot = telebot.TeleBot(settings.bot_token, parse_mode="HTML")
