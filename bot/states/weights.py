"""
FSM состояния для работы с весами.
"""

from telebot.handler_backends import State, StatesGroup


class WeightStates(StatesGroup):
    """Состояния процесса работы с весами."""

    waiting_action = State()  # Ожидание выбора действия
    waiting_exercise_choice = State()  # Выбор упражнения из списка
    waiting_exercise_input = State()  # Ввод упражнения вручную
    waiting_date = State()  # Ввод даты
    waiting_weight = State()  # Ввод веса
    waiting_progress_exercise = State()  # Выбор упражнения для прогресса
