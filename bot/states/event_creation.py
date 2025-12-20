"""
FSM состояния для создания события.
"""

from telebot.handler_backends import State, StatesGroup


class EventCreationStates(StatesGroup):
    """Состояния процесса создания события."""

    waiting_title = State()  # Ожидание названия
    waiting_date = State()  # Ожидание даты
    waiting_location = State()  # Ожидание места
    waiting_sport_type = State()  # Ожидание вида спорта
    waiting_max_participants = State()  # Ожидание количества участников
    waiting_fee = State()  # Ожидание взноса
    waiting_note = State()  # Ожидание примечания
