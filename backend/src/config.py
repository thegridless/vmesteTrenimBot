"""
Конфигурация приложения.
Загрузка переменных окружения через pydantic-settings.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Настройки приложения."""

    # База данных
    database_url: str = "sqlite+aiosqlite:///./app.db"

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = False

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
