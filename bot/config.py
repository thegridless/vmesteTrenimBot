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
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
