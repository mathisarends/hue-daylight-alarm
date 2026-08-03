from huerise.presentation import Feature

from .infrastructure.di import (
    AlarmProvider,
    DatabaseProvider,
    SchedulerProvider,
    StorageProvider,
)
from .presentation import alarm_router, register_alarm_exception_handlers

feature = Feature(
    name="alarm",
    routers=[alarm_router],
    providers=[
        DatabaseProvider,
        StorageProvider,
        AlarmProvider,
        SchedulerProvider,
    ],
    register_exception_handlers=register_alarm_exception_handlers,
)

__all__ = ["feature"]
