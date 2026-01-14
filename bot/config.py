"""
Конфигурация Telegram бота.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Настройки бота."""

    # Telegram
    bot_token: str = ""

    # Backend API
    api_base_url: str = "http://localhost:8000/api/v1"

    # Режим отладки
    debug: bool = False

    class Config:
        # Используем переменные окружения (передаются через docker-compose)
        # env_file опционален для локальной разработки
        env_file = ".env"
        env_file_encoding = "utf-8"
        # Приоритет: переменные окружения > env_file
        case_sensitive = False
        # Разрешаем дополнительные поля из .env (например, POSTGRES_*)
        extra = "ignore"


settings = Settings()
