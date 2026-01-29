"""
Слой репозиториев для работы с БД.
Инкапсулирует CRUD-операции и предоставляет абстракцию над SQLAlchemy.
"""

from .base import BaseRepository

__all__ = ["BaseRepository"]
