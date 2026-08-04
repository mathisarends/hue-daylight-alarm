from collections.abc import Iterator
from datetime import timedelta

from huerise.features.alarm.domain import SunriseConfig

# Sending brightness updates faster than this gains nothing: the Hue bridge
# rate-limits and coalesces them. Step count is therefore derived, never stored.
STEP_INTERVAL = timedelta(seconds=6)


def sunrise_steps(
    config: SunriseConfig, step_interval: timedelta = STEP_INTERVAL
) -> Iterator[int]:
    """Brightness values from start to end, one per ``step_interval``."""
    total_seconds = config.duration.total_seconds()
    steps = max(int(total_seconds // step_interval.total_seconds()), 1)
    span = config.brightness_end - config.brightness_start

    for step in range(steps):
        yield config.brightness_start + round(span * step / max(steps - 1, 1))
