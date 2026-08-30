from huerise.presentation import Feature

from . import alarm, auth, events, lighting, runner, scheduler, user

FEATURES: tuple[Feature, ...] = (
    user.feature,
    auth.feature,
    alarm.feature,
    lighting.feature,
    events.feature,
    runner.feature,
    scheduler.feature,
)

__all__ = ["FEATURES"]
