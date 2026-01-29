"""
FSM состояния для администрирования.
"""

from telebot.handler_backends import State, StatesGroup


class AdminStates(StatesGroup):
    """Состояния администрирования."""

    waiting_broadcast_text = State()
    waiting_broadcast_confirm = State()
    waiting_personal_select = State()
    waiting_personal_text = State()
    waiting_personal_confirm = State()
