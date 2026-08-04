from huerise.presentation import Feature

from . import alarm, devices, runner, scheduler

FEATURES: tuple[Feature, ...] = (
    alarm.feature,
    devices.feature,
    runner.feature,
    scheduler.feature,
)

__all__ = ["FEATURES"]
