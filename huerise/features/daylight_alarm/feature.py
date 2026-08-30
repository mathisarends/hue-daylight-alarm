from huerise.presentation import Feature

from .provider import DaylightAlarmProvider
from .router import router

feature = Feature(
    name="daylight_alarm",
    routers=[router],
    providers=[DaylightAlarmProvider],
)
