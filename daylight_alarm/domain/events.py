from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from daylight_alarm.domain.value_objects import Brightness


@dataclass(frozen=True)
class DomainEvent:
    aggregate_id: UUID
    occurred_at: datetime


@dataclass(frozen=True)
class AlarmStarted(DomainEvent):
    room_name: str
    scene_name: str


@dataclass(frozen=True)
class BrightnessChangeRequested(DomainEvent):
    room_name: str
    brightness: Brightness
    step_number: int
    total_steps: int


@dataclass(frozen=True)
class WaitRequested(DomainEvent):
    duration_seconds: float


@dataclass(frozen=True)
class AlarmCompleted(DomainEvent):
    room_name: str
    total_steps: int


@dataclass(frozen=True)
class AlarmCancelled(DomainEvent):
    room_name: str
    at_step: int