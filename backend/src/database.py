"""
Настройка подключения к базе данных.
SQLAlchemy async engine и session factory.
"""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from src.config import settings

# Async engine для SQLite
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
)

# Фабрика сессий
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Базовый класс для всех моделей."""

    pass


async def get_session() -> AsyncSession:
    """
    Dependency для получения сессии БД.
    Используется в FastAPI endpoints.
    """
    async with async_session_maker() as session:
        yield session
