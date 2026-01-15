"""
Точка входа Telegram бота.
"""

import asyncio

import httpx
from config import settings
from handlers import register_all_handlers
from loguru import logger
from middleware import log_message_middleware

from bot import bot


async def check_api_connection() -> bool:
    """Проверка подключения к Backend API при старте."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{settings.api_base_url.replace('/api/v1', '')}/health")
            if response.status_code == 200:
                logger.info(f"✅ Backend API доступен: {settings.api_base_url}")
                return True
            logger.warning(f"⚠️ Backend API вернул статус {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"❌ Backend API недоступен ({settings.api_base_url}): {e}")
        return False


def main():
    """Запуск бота."""
    logger.info("🤖 Запуск бота...")
    logger.info(f"📡 API: {settings.api_base_url}")

    # Проверяем подключение к API
    if not asyncio.run(check_api_connection()):
        logger.warning("⚠️ Продолжаем запуск без проверки API")

    # Регистрируем middleware и обработчики
    log_message_middleware(bot)
    register_all_handlers(bot)

    logger.info("✅ Обработчики зарегистрированы")
    logger.info("🚀 Бот запущен!")

    try:
        bot.infinity_polling(timeout=60, long_polling_timeout=60)
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        raise


if __name__ == "__main__":
    main()
