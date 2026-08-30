from huerise.presentation import Feature

from .daylight_alarm.feature import feature as daylight_alarm
from .lighting.feature import feature as lighting

FEATURES: tuple[Feature, ...] = (
    lighting,
    daylight_alarm,
)

__all__ = ["FEATURES"]
