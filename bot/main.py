"""
Точка входа Telegram бота.
"""

from loguru import logger

from bot import bot
from config import settings
from handlers import register_all_handlers

# Настраиваем логгер
from logger import setup_logger
from middleware import log_message_middleware

setup_logger()


def check_api_connection():
    """Проверка подключения к Backend API при старте."""
    try:
        import httpx

        response = httpx.get(f"{settings.api_base_url.replace('/api/v1', '')}/health", timeout=5.0)
        if response.status_code == 200:
            logger.info(f"✅ Подключение к Backend API успешно: {settings.api_base_url}")
            return True
        else:
            logger.warning(f"⚠️  Backend API вернул статус {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"❌ Не удалось подключиться к Backend API ({settings.api_base_url}): {e}")
        logger.error("Убедитесь, что Backend запущен и доступен")
        return False


def main():
    """Запуск бота."""
    logger.info("🤖 Бот запускается...")
    logger.info(f"📡 API URL: {settings.api_base_url}")

    # Проверяем подключение к API
    if not check_api_connection():
        logger.warning("⚠️  Продолжаем запуск, но возможны проблемы с API")

    # Регистрируем middleware для логирования
    log_message_middleware(bot)
    logger.info("✅ Middleware для логирования зарегистрирован")

    # Регистрируем обработчики
    register_all_handlers(bot)

    logger.info("✅ Обработчики зарегистрированы")
    logger.info("🚀 Бот запущен и ожидает сообщения...")

    # Запускаем polling
    try:
        bot.infinity_polling(timeout=60, long_polling_timeout=60)
    except Exception as e:
        logger.error(f"❌ Ошибка бота: {e}")
        raise


if __name__ == "__main__":
    main()
