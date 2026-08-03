from huerise.presentation import Feature

from .infrastructure.di import AlarmProvider
from .presentation import alarm_router, register_alarm_exception_handlers

feature = Feature(
    name="alarm",
    routers=[alarm_router],
    providers=[AlarmProvider],
    register_exception_handlers=register_alarm_exception_handlers,
)

__all__ = ["feature"]
