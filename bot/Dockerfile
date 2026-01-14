FROM python:3.13-slim

WORKDIR /app

# Установка uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Копируем файлы зависимостей из корня проекта
COPY pyproject.toml uv.lock README.md ./

# Устанавливаем зависимости с группой bot
RUN uv sync --frozen --no-dev --group bot

# Копируем исходный код bot
COPY bot/ ./bot/

# Копируем .env файл для использования в контейнере (если существует)
# Переменные также передаются через docker-compose env_file
COPY .env ./.env

# Устанавливаем рабочую директорию для bot
WORKDIR /app/bot

# Запуск бота
# Используем --directory /app для uv (где находится pyproject.toml)
# Запускаем с абсолютным путём к main.py и правильным PYTHONPATH
CMD ["sh", "-c", "PYTHONPATH=/app/bot uv run --directory /app python /app/bot/main.py"]
