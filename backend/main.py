"""
Точка входа FastAPI приложения.
"""

from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request
from loguru import logger

from src.admin import setup_admin
from src.config import settings
from src.database import engine
from src.events.router import router as events_router
from src.sports.router import router as sports_router
from src.users.router import router as users_router


@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: ARG001
    """
    Lifecycle событий приложения.
    Создаёт таблицы при запуске (для разработки).
    """
    logger.info("🚀 Запуск приложения...")

    logger.info(f"📡 API доступен на http://{settings.api_host}:{settings.api_port}")

    yield

    # При завершении
    logger.info("🛑 Остановка приложения...")
    await engine.dispose()


app = FastAPI(
    title="VmesteTrenim API",
    description="API для приложения совместных тренировок",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Подключаем роутеры
app.include_router(users_router, prefix="/api/v1")
app.include_router(sports_router, prefix="/api/v1")
app.include_router(events_router, prefix="/api/v1")

# Настраиваем админ-панель
admin = setup_admin(app)
logger.info("✅ Админ-панель доступна на http://localhost:8000/admin")


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Middleware для логирования HTTP запросов."""
    logger.debug(f"➡️  {request.method} {request.url.path}")
    response = await call_next(request)
    logger.debug(f"⬅️  {request.method} {request.url.path} → {response.status_code}")
    return response


@app.get("/health")
async def health_check():
    """Проверка работоспособности сервиса."""
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
    )
