"""
Инициализация Telegram бота.
"""

import telebot
from config import settings
from telebot import apihelper

# Включаем middleware (необходимо до создания экземпляра бота)
apihelper.ENABLE_MIDDLEWARE = True

# Создаём экземпляр бота
bot = telebot.TeleBot(settings.bot_token, parse_mode="HTML")
