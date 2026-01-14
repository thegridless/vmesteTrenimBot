FROM python:3.13-slim

WORKDIR /app

# Установка uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Копируем файлы зависимостей из корня проекта
COPY pyproject.toml uv.lock README.md ./

# Устанавливаем зависимости с группой api
RUN uv sync --frozen --no-dev --group api

# Копируем исходный код backend
COPY backend/ ./backend/

# Устанавливаем рабочую директорию для backend
WORKDIR /app/backend

# Открываем порт
EXPOSE 8000

# Запуск приложения
# Используем --directory /app для uv (где находится pyproject.toml)
# Запускаем uvicorn из рабочей директории /app/backend
CMD ["sh", "-c", "cd /app/backend && PYTHONPATH=/app/backend uv run --directory /app python -m uvicorn main:app --host 0.0.0.0 --port 8000"]
