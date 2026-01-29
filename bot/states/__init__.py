"""
FSM состояния для бота.
"""

from states.admin import AdminStates
from states.event_creation import EventCreationStates
from states.registration import RegistrationStates
from states.weights import WeightStates

__all__ = ["AdminStates", "RegistrationStates", "EventCreationStates", "WeightStates"]
