from dataclasses import dataclass
from enum import IntEnum, StrEnum


class Weekday(IntEnum):
    MON = 0
    TUE = 1
    WED = 2
    THU = 3
    FRI = 4
    SAT = 5
    SUN = 6


class AlarmStatus(StrEnum):
    SCHEDULED = "scheduled"
    INTRO = "intro"
    SUNRISE = "sunrise"
    RINGING = "ringing"
    COMPLETED = "completed"
    INACTIVE = "inactive"
    CANCELLED = "cancelled"


class AlarmType(StrEnum):
    ONE_TIME = "one_time"
    RECURRING = "recurring"


@dataclass(frozen=True)
class Schedule:
    hour: int
    minute: int
    recurrence: frozenset[Weekday] | None = None

    def __post_init__(self) -> None:
        if not (0 <= self.hour <= 23):
            raise ValueError("Hour must be 0-23")
        if not (0 <= self.minute <= 59):
            raise ValueError("Minute must be 0-59")

    def is_recurring(self) -> bool:
        return self.recurrence is not None


@dataclass(frozen=True)
class IntroConfig:
    audio_file: str


@dataclass(frozen=True)
class SunriseConfig:
    room_name: str
    scene_name: str = "Tageslichtwecker"
    duration_minutes: int = 7
    brightness_start: int = 1
    brightness_end: int = 100
    steps: int = 70

    def __post_init__(self) -> None:
        if not (1 <= self.brightness_start < self.brightness_end <= 100):
            raise ValueError("Invalid brightness range")
        if self.steps < 1:
            raise ValueError("steps must be >= 1")

    @property
    def step_interval_seconds(self) -> float:
        return (self.duration_minutes * 60) / self.steps


@dataclass(frozen=True)
class RingtoneConfig:
    audio_file: str
    volume: int = 80

    def __post_init__(self) -> None:
        if not (0 <= self.volume <= 100):
            raise ValueError("volume must be 0-100")
