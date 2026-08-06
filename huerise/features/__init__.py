from huerise.presentation import Feature

from . import alarm, auth, devices, events, runner, scheduler, user

FEATURES: tuple[Feature, ...] = (
    user.feature,
    auth.feature,
    alarm.feature,
    devices.feature,
    events.feature,
    runner.feature,
    scheduler.feature,
)

__all__ = ["FEATURES"]
