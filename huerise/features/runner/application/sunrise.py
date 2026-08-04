from collections.abc import Iterator
from datetime import timedelta

from huerise.features.alarm.domain import SunriseSettings

# Sending brightness updates faster than this gains nothing: the Hue bridge
# rate-limits and coalesces them. Step count is therefore derived, never stored.
STEP_INTERVAL = timedelta(seconds=6)


def sunrise_steps(
    settings: SunriseSettings, step_interval: timedelta = STEP_INTERVAL
) -> Iterator[int]:
    """Brightness values from start to end, one per ``step_interval``."""
    total_seconds = settings.duration.total_seconds()
    steps = max(int(total_seconds // step_interval.total_seconds()), 1)
    span = settings.brightness_end - settings.brightness_start

    for step in range(steps):
        yield settings.brightness_start + round(span * step / max(steps - 1, 1))
