"""
FSM состояния для регистрации пользователя.
"""

from telebot.handler_backends import State, StatesGroup


class RegistrationStates(StatesGroup):
    """Состояния процесса регистрации."""

    waiting_age = State()  # Ожидание возраста
    waiting_gender = State()  # Ожидание пола
    waiting_city = State()  # Ожидание города
    waiting_sports = State()  # Ожидание видов спорта
