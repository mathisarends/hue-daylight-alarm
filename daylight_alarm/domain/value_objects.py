from dataclasses import dataclass


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
