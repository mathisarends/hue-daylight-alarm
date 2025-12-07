from datetime import datetime
from enum import StrEnum
from typing import Callable
from uuid import uuid4

from daylight_alarm.domain.events import (
    AlarmCancelled, 
    AlarmCompleted, 
    AlarmStarted, 
    BrightnessChangeRequested, 
    DomainEvent, 
    WaitRequested
)
from daylight_alarm.domain.value_objects import (
    Brightness, 
    BrightnessRange, 
    Duration, 
    TransitionSteps
)
from uuid import uuid4


class AlarmStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class SunriseAlarm:
    def __init__(
        self,
        room_name: str = "",
        scene_name: str = "Tageslichtwecker",
        duration: Duration = None,
        brightness_range: BrightnessRange = None,
        steps: TransitionSteps = None,
        easing_function: Callable[[float], float] = None,
    ):
        self.id = uuid4()
        self.room_name = room_name
        self.scene_name = scene_name
        self.duration = duration if duration is not None else Duration(minutes=7)
        self.brightness_range = (
            brightness_range if brightness_range is not None else BrightnessRange(start=1, end=100)
        )
        self.steps = steps if steps is not None else TransitionSteps(count=70)
        self.easing_function = easing_function if easing_function is not None else (lambda t: t)

        self.status = AlarmStatus.PENDING
        self.current_step = 0
        self._domain_events: list[DomainEvent] = []

    def collect_events(self) -> list["DomainEvent"]:
        events = self._domain_events.copy()
        self._domain_events.clear()
        return events

    def _raise_event(self, event: "DomainEvent") -> None:
        self._domain_events.append(event)

    def can_start(self) -> bool:
        return self.status == AlarmStatus.PENDING

    def can_cancel(self) -> bool:
        return self.status == AlarmStatus.RUNNING

    def can_progress(self) -> bool:
        return self.status == AlarmStatus.RUNNING

    def start(self) -> None:
        if not self.can_start():
            raise ValueError(f"Cannot start alarm in status {self.status}")

        self.status = AlarmStatus.RUNNING
        self._raise_event(AlarmStarted(
            aggregate_id=self.id,
            occurred_at=datetime.now(),
            room_name=self.room_name,
            scene_name=self.scene_name
        ))

    def progress_step(self) -> None:
        if not self.can_progress():
            raise ValueError(f"Cannot progress alarm in status {self.status}")

        brightness = self._calculate_brightness_for_step(self.current_step)

        self._raise_event(BrightnessChangeRequested(
            aggregate_id=self.id,
            occurred_at=datetime.now(),
            room_name=self.room_name,
            brightness=Brightness(percentage=brightness),
            step_number=self.current_step,
            total_steps=self.steps.count
        ))

        if self.current_step < self.steps.count:
            step_duration = self.duration.seconds / self.steps.count
            self._raise_event(WaitRequested(
                aggregate_id=self.id,
                occurred_at=datetime.now(),
                duration_seconds=step_duration
            ))

        self.current_step += 1

        if self.current_step > self.steps.count:
            self._complete()

    def cancel(self) -> None:
        if not self.can_cancel():
            raise ValueError(f"Cannot cancel alarm in status {self.status}")

        self.status = AlarmStatus.CANCELLED
        self._raise_event(AlarmCancelled(
            aggregate_id=self.id,
            occurred_at=datetime.now(),
            room_name=self.room_name,
            at_step=self.current_step
        ))

    def _complete(self) -> None:
        self.status = AlarmStatus.COMPLETED
        self._raise_event(AlarmCompleted(
            aggregate_id=self.id,
            occurred_at=datetime.now(),
            room_name=self.room_name,
            total_steps=self.steps.count
        ))

    def _calculate_brightness_for_step(self, step: int) -> int:
        progress = step / self.steps.count
        eased_progress = self.easing_function(progress)
        brightness = self.brightness_range.start + (
            self.brightness_range.range * eased_progress
        )
        return int(brightness)

    @property
    def is_finished(self) -> bool:
        return self.status in (AlarmStatus.COMPLETED, AlarmStatus.CANCELLED)