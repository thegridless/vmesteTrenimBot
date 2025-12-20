"""
FSM состояния для бота.
"""

from states.event_creation import EventCreationStates
from states.registration import RegistrationStates

__all__ = ["RegistrationStates", "EventCreationStates"]
