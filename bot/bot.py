"""
Инициализация Telegram бота.
"""

import telebot
from telebot import apihelper

from config import settings

# Включаем middleware (необходимо до создания экземпляра бота)
apihelper.ENABLE_MIDDLEWARE = True

# Создаём экземпляр бота
bot = telebot.TeleBot(settings.bot_token, parse_mode="HTML")
