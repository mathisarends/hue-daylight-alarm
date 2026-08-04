from collections.abc import Iterator
from dataclasses import dataclass
from datetime import timedelta

# Sending brightness updates faster than this gains nothing: the Hue bridge
# rate-limits and coalesces them. Step count is therefore derived, never stored.
STEP_INTERVAL = timedelta(seconds=6)


@dataclass(frozen=True, slots=True)
class SunriseRamp:
    """A brightness climb over time -- the light half of a sunrise, on its own.

    An alarm profile carries one of these alongside a scene; a demo builds one
    on the spot. Both feed the same :func:`sunrise_steps`, so what a user
    previews is the curve they will wake up to.
    """

    duration: timedelta
    brightness_start: int = 1
    brightness_end: int = 100

    def __post_init__(self) -> None:
        if not (1 <= self.brightness_start < self.brightness_end <= 100):
            raise ValueError("Invalid brightness range")
        if self.duration < timedelta(0):
            raise ValueError("duration must not be negative")


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
    ramp: SunriseRamp, step_interval: timedelta = STEP_INTERVAL
) -> Iterator[SunriseStep]:
    """Brightness values from start to end, one per ``step_interval``."""
    total_seconds = ramp.duration.total_seconds()
    steps = max(int(total_seconds // step_interval.total_seconds()), 1)
    span = ramp.brightness_end - ramp.brightness_start

    for step in range(steps):
        yield SunriseStep(
            index=step,
            total=steps,
            brightness=ramp.brightness_start + round(span * step / max(steps - 1, 1)),
            interval=step_interval,
        )
