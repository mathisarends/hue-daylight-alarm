from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
import random


@dataclass(frozen=True)
class Duration:
    minutes: int

    def __post_init__(self):
        if self.minutes <= 0:
            raise ValueError("Duration must be positive")

    @property
    def seconds(self) -> float:
        return self.minutes * 60


@dataclass(frozen=True)
class BrightnessRange:
    start: int
    end: int

    def __post_init__(self):
        if not (0 <= self.start <= 100):
            raise ValueError("Start brightness must be between 0 and 100")
        if not (0 <= self.end <= 100):
            raise ValueError("End brightness must be between 0 and 100")
        if self.start >= self.end:
            raise ValueError("Start brightness must be less than end brightness")

    @property
    def range(self) -> int:
        return self.end - self.start


@dataclass(frozen=True)
class TransitionSteps:
    count: int

    def __post_init__(self):
        if self.count <= 0:
            raise ValueError("Steps must be positive")


@dataclass(frozen=True)
class Brightness:
    percentage: int

    def __post_init__(self):
        if not (0 <= self.percentage <= 100):
            raise ValueError("Brightness must be between 0 and 100")


class EasingType(StrEnum):
    LINEAR = "linear"
    EASE_IN_QUAD = "ease_in_quad"
    EASE_IN_CUBIC = "ease_in_cubic"


@dataclass(frozen=True)
class AudioFile:
    path: Path

    def __post_init__(self):
        if not self.path.exists():
            raise ValueError(f"Audio file does not exist: {self.path}")
        if self.path.suffix.lower() not in [".mp3", ".wav", ".ogg", ".flac"]:
            raise ValueError(f"Unsupported audio format: {self.path.suffix}")


@dataclass(frozen=True)
class SoundProfile:
    name: str
    wake_up_sound: AudioFile
    get_up_sound: AudioFile
    description: str = ""

    def __str__(self) -> str:
        return f"{self.name}: {self.wake_up_sound.path.stem} → {self.get_up_sound.path.stem}"


class SoundProfileName(StrEnum):
    PEACEFUL = "peaceful"
    ENERGETIC = "energetic"
    NATURE = "nature"
    COSMIC = "cosmic"
    MYSTICAL = "mystical"
    GENTLE = "gentle"


@dataclass(frozen=True)
class AlarmSounds:
    completion_sound: AudioFile
    startup_sound: AudioFile | None = None

    def __post_init__(self):
        if self.completion_sound is None:
            raise ValueError("Completion sound is required")


@dataclass(frozen=True)
class AudioDirectory:
    path: Path
    supported_formats: tuple[str, ...] = (".mp3", ".wav", ".ogg", ".flac")

    def __post_init__(self):
        if not self.path.exists():
            raise ValueError(f"Audio directory does not exist: {self.path}")
        if not self.path.is_dir():
            raise ValueError(f"Path is not a directory: {self.path}")

        if not self.get_audio_files():
            raise ValueError(f"No audio files found in: {self.path}")

    def get_audio_files(self) -> list[Path]:
        audio_files = []
        for ext in self.supported_formats:
            audio_files.extend(self.path.glob(f"*{ext}"))
        return sorted(audio_files)

    def get_random_file(self) -> AudioFile:
        files = self.get_audio_files()
        if not files:
            raise ValueError(f"No audio files found in: {self.path}")
        return AudioFile(path=random.choice(files))


class AlarmStatus(StrEnum):
    SCHEDULED = "scheduled"
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class ScheduledTime:
    hour: int
    minute: int

    def __post_init__(self):
        if not (0 <= self.hour <= 23):
            raise ValueError("Hour must be between 0 and 23")
        if not (0 <= self.minute <= 59):
            raise ValueError("Minute must be between 0 and 59")

    def to_seconds_from_midnight(self) -> int:
        return self.hour * 3600 + self.minute * 60

    def __str__(self) -> str:
        return f"{self.hour:02d}:{self.minute:02d}"
