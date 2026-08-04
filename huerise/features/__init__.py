from huerise.presentation import Feature

from . import alarm, devices, events, runner, scheduler

FEATURES: tuple[Feature, ...] = (
    alarm.feature,
    devices.feature,
    events.feature,
    runner.feature,
    scheduler.feature,
)

__all__ = ["FEATURES"]
