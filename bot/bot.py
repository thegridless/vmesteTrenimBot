"""
Инициализация Telegram бота.
"""

import telebot
from config import settings
from telebot import apihelper
from telebot.storage import StateMemoryStorage

# Включаем middleware (необходимо до создания экземпляра бота)
apihelper.ENABLE_MIDDLEWARE = True

# Создаём хранилище состояний
state_storage = StateMemoryStorage()

# Создаём экземпляр бота
bot = telebot.TeleBot(settings.bot_token, parse_mode="HTML", state_storage=state_storage)
