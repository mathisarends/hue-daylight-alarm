from huerise.shared import Feature

from .infrastructure import DaylightAlarmProvider
from .presentation import router

feature = Feature(
    name="daylight_alarm",
    routers=[router],
    providers=[DaylightAlarmProvider],
)
