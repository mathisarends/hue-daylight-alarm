from huerise.presentation import Feature

from .infrastructure import SchedulerProvider

feature = Feature(name="scheduler", providers=[SchedulerProvider])

__all__ = ["feature"]
