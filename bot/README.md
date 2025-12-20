# Bot — Telegram 🤖

Telegram бот на pyTelegramBotAPI для взаимодействия с пользователями.

## 📁 Структура

```
bot/
├── main.py             # Точка входа, запуск polling
├── bot.py              # Инициализация TeleBot
├── config.py           # Настройки (pydantic-settings)
├── logger.py           # Настройка loguru
├── api_client.py       # HTTP клиент для Backend API
├── pyproject.toml      # Зависимости
├── handlers/           # Обработчики сообщений
│   ├── __init__.py     # Регистрация всех handlers
│   └── start.py        # /start, /help, меню
├── keyboards/          # Клавиатуры
│   ├── __init__.py
│   └── main_menu.py    # Главное меню
├── states/             # FSM состояния (заготовка)
│   └── __init__.py
└── Dockerfile          # Docker образ
```

## 🔄 Архитектура

```
┌─────────────────┐     HTTP      ┌─────────────────┐
│  Telegram User  │ ◄──────────►  │   Telegram API  │
└─────────────────┘               └────────┬────────┘
                                           │
                                           ▼
                                  ┌─────────────────┐
                                  │       Bot       │
                                  │  (polling mode) │
                                  └────────┬────────┘
                                           │ HTTP
                                           ▼
                                  ┌─────────────────┐
                                  │  Backend API    │
                                  │   (FastAPI)     │
                                  └─────────────────┘
```

## 🎮 Команды и функции

| Команда/Кнопка | Описание |
|----------------|----------|
| `/start` | Регистрация и главное меню |
| `/help` | Справка по боту |
| 📋 Мои тренировки | Список тренировок пользователя |
| 🔍 Найти тренировку | Поиск доступных тренировок |
| ➕ Создать тренировку | Создание нового мероприятия |
| 👤 Профиль | Информация о пользователе |

## 🚀 Запуск

```bash
# Установка зависимостей
uv sync

# Запуск бота
uv run python main.py
```

## 🔧 Переменные окружения

Создайте файл `.env`:

**Для локального запуска:**
```env
# Токен бота (получить у @BotFather)
BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz

# URL Backend API (локальный)
API_BASE_URL=http://localhost:8000/api/v1

# Режим отладки
DEBUG=true
```

**Для Docker (в deployment/.env):**
```env
BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz

# URL Backend API (имя сервиса Docker)
API_BASE_URL=http://backend:8000/api/v1

DEBUG=false
```

> **Важно**: При локальном запуске используйте `localhost:8000`, в Docker - `backend:8000` (имя сервиса из docker-compose).

## 📦 Зависимости

- **pyTelegramBotAPI** — Telegram Bot API
- **httpx** — HTTP клиент для запросов к backend
- **pydantic-settings** — Управление конфигурацией
- **loguru** — Логирование

## 🔌 API Client

`api_client.py` предоставляет методы для работы с Backend:

```python
from api_client import api_client

# Пользователи
api_client.get_or_create_user(telegram_id, username, first_name)
api_client.get_user_by_telegram_id(telegram_id)

# Мероприятия
api_client.get_events(skip, limit, creator_id)
api_client.get_event(event_id)
api_client.create_event(title, date, creator_id, description, location)

# Участие
api_client.join_event(event_id, user_id)
api_client.leave_event(event_id, user_id)
api_client.get_user_events(user_id)
```

## 📝 Добавление нового handler

1. Создайте файл в `handlers/`:

```python
# handlers/events.py
from loguru import logger
from telebot import TeleBot
from telebot.types import Message

def register_event_handlers(bot: TeleBot):
    @bot.message_handler(commands=["events"])
    def cmd_events(message: Message):
        logger.info(f"Команда /events от {message.from_user.id}")
        # ...
```

2. Зарегистрируйте в `handlers/__init__.py`:

```python
from handlers.start import register_start_handlers
from handlers.events import register_event_handlers

def register_all_handlers(bot):
    register_start_handlers(bot)
    register_event_handlers(bot)
```
