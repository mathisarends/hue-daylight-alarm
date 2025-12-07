from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path


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
        

@dataclass(frozen=True)
class AudioFile:
    path: Path
    
    def __post_init__(self):
        if not self.path.exists():
            raise ValueError(f"Audio file does not exist: {self.path}")
        if self.path.suffix not in ['.mp3', '.wav', '.ogg']:
            raise ValueError(f"Unsupported audio format: {self.path.suffix}")


@dataclass(frozen=True)
class AlarmSounds:
    startup_sound: AudioFile | None = None
    completion_sound: AudioFile
    
    def __post_init__(self):
        if self.completion_sound is None:
            raise ValueError("Completion sound is required")


class AlarmStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    CANCELLED = "cancelled"