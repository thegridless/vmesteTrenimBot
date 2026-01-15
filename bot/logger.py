"""
Настройка логирования через loguru.
"""

import sys

from config import settings
from loguru import logger


def setup_logger():
    """Настройка loguru. Уровень логирования зависит от DEBUG."""
    logger.remove()

    log_level = "DEBUG" if settings.debug else "INFO"

    # Консольный вывод
    logger.add(
        sys.stderr,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level=log_level,
        colorize=True,
    )

    # Файловый лог для продакшена
    if not settings.debug:
        logger.add(
            "logs/bot.log",
            rotation="10 MB",
            retention="7 days",
            level="INFO",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
        )

    return logger


setup_logger()
