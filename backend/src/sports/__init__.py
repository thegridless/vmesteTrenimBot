"""
Модуль для работы с видами спорта.
"""

from src.sports.models import Sport
from src.sports.repository import SportRepository
from src.sports.router import router

__all__ = ["Sport", "SportRepository", "router"]
