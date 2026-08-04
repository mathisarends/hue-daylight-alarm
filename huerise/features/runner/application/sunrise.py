from collections.abc import Iterator
from dataclasses import dataclass
from datetime import timedelta

from huerise.features.alarm.domain import SunriseConfig

# Sending brightness updates faster than this gains nothing: the Hue bridge
# rate-limits and coalesces them. Step count is therefore derived, never stored.
STEP_INTERVAL = timedelta(seconds=6)


@dataclass(frozen=True, slots=True)
class SunriseStep:
    """One brightness change, aware of where it sits in the whole sunrise."""

    index: int
    total: int
    brightness: int
    interval: timedelta

    @property
    def elapsed_seconds(self) -> int:
        return round(self.index * self.interval.total_seconds())

    @property
    def total_seconds(self) -> int:
        return round(self.total * self.interval.total_seconds())


def sunrise_steps(
    config: SunriseConfig, step_interval: timedelta = STEP_INTERVAL
) -> Iterator[SunriseStep]:
    """Brightness values from start to end, one per ``step_interval``."""
    total_seconds = config.duration.total_seconds()
    steps = max(int(total_seconds // step_interval.total_seconds()), 1)
    span = config.brightness_end - config.brightness_start

    for step in range(steps):
        yield SunriseStep(
            index=step,
            total=steps,
            brightness=config.brightness_start + round(span * step / max(steps - 1, 1)),
            interval=step_interval,
        )
