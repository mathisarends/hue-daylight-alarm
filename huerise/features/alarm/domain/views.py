from dataclasses import dataclass, field
from datetime import UTC, datetime, time, timedelta
from enum import IntEnum, StrEnum
from uuid import UUID
from zoneinfo import ZoneInfo

DEFAULT_TIMEZONE = ZoneInfo("Europe/Berlin")

_DAYS_IN_WEEK = 7


class Weekday(IntEnum):
    MON = 0
    TUE = 1
    WED = 2
    THU = 3
    FRI = 4
    SAT = 5
    SUN = 6


class OccurrenceState(StrEnum):
    PENDING = "pending"
    SUNRISE = "sunrise"
    RINGING = "ringing"
    SNOOZED = "snoozed"
    DISMISSED = "dismissed"
    SKIPPED = "skipped"
    FAILED = "failed"


@dataclass(frozen=True)
class Schedule:
    """A wall-clock wake-up rule in a specific IANA timezone.

    The alarm time is never stored as a UTC instant: 07:00 must stay 07:00 local
    across DST transitions. Concrete instants are derived on demand via
    :meth:`next_occurrence`.
    """

    hour: int
    minute: int
    tz: ZoneInfo = DEFAULT_TIMEZONE
    weekdays: frozenset[Weekday] = field(default_factory=frozenset)

    def __post_init__(self) -> None:
        if not (0 <= self.hour <= 23):
            raise ValueError("Hour must be 0-23")
        if not (0 <= self.minute <= 59):
            raise ValueError("Minute must be 0-59")

    @property
    def is_recurring(self) -> bool:
        return bool(self.weekdays)

    @property
    def tz_name(self) -> str:
        return self.tz.key

    @property
    def recurrence_mask(self) -> int:
        return sum(1 << int(day) for day in self.weekdays)

    @classmethod
    def from_mask(
        cls, hour: int, minute: int, tz: ZoneInfo, recurrence_mask: int
    ) -> Schedule:
        weekdays = frozenset(
            Weekday(day) for day in range(_DAYS_IN_WEEK) if recurrence_mask >> day & 1
        )
        return cls(hour=hour, minute=minute, tz=tz, weekdays=weekdays)

    def next_occurrence(self, after: datetime) -> datetime:
        """First UTC instant strictly after ``after`` matching this rule.

        ``after`` must be timezone-aware. A one-time schedule (no weekdays)
        matches the next calendar day carrying the wall-clock time.
        """
        if after.tzinfo is None:
            raise ValueError("`after` must be timezone-aware")

        local_date = after.astimezone(self.tz).date()
        # Scan one extra day: the local wall time may still resolve to an
        # instant before `after` on the first candidate day.
        for offset in range(_DAYS_IN_WEEK + 1):
            day = local_date + timedelta(days=offset)
            if self.is_recurring and Weekday(day.weekday()) not in self.weekdays:
                continue
            candidate = self._resolve(day)
            if candidate > after:
                return candidate

        raise AssertionError("Unreachable: a schedule always has a next occurrence")

    def _resolve(self, day) -> datetime:
        """Map a local calendar day to the UTC instant this alarm should fire.

        DST edge cases, both handled by ``fold=0``:

        * Spring forward -- 02:30 does not exist. ``fold=0`` uses the offset
          from *before* the transition, so the alarm fires at the instant it
          would have without the jump (locally 03:30).
        * Fall back -- 02:30 exists twice. ``fold=0`` picks the first one, so
          the alarm fires once, at the earlier of the two.
        """
        local = datetime.combine(day, time(self.hour, self.minute)).replace(
            tzinfo=self.tz, fold=0
        )
        return local.astimezone(UTC)


@dataclass(frozen=True)
class IntroConfig:
    sound_id: UUID


@dataclass(frozen=True)
class SunriseConfig:
    scene_name: str = "Tageslichtwecker"
    duration: timedelta = timedelta(minutes=7)
    brightness_start: int = 1
    brightness_end: int = 100

    def __post_init__(self) -> None:
        if not (1 <= self.brightness_start < self.brightness_end <= 100):
            raise ValueError("Invalid brightness range")
        if self.duration < timedelta(0):
            raise ValueError("duration must not be negative")

    @property
    def duration_minutes(self) -> int:
        return int(self.duration.total_seconds() // 60)


@dataclass(frozen=True)
class RingtoneConfig:
    sound_id: UUID
    volume: int = 80

    def __post_init__(self) -> None:
        if not (0 <= self.volume <= 100):
            raise ValueError("volume must be 0-100")
