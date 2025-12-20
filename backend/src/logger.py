"""
Настройка логирования через loguru.
"""

import sys

from loguru import logger

from src.config import settings


def setup_logger():
    """
    Настройка loguru.
    Уровень логирования зависит от DEBUG в .env.
    """
    # Удаляем стандартный handler
    logger.remove()

    # Определяем уровень логирования
    log_level = "DEBUG" if settings.debug else "INFO"

    # Добавляем handler с форматированием
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>",
        level=log_level,
        colorize=True,
    )

    # Логирование в файл (опционально, для продакшена)
    if not settings.debug:
        logger.add(
            "logs/app.log",
            rotation="10 MB",
            retention="7 days",
            level="INFO",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
        )

    return logger


# Инициализируем при импорте
setup_logger()
