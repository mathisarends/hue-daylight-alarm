from datetime import datetime
from typing import Callable
from uuid import UUID, uuid4

from daylight_alarm.domain.events import (
    AlarmCancelled, 
    AlarmCompleted, 
    AlarmStarted, 
    BrightnessChangeRequested, 
    DomainEvent, 
    WaitRequested
)
from daylight_alarm.domain.value_objects import (
    AlarmStatus,
    Brightness, 
    BrightnessRange, 
    Duration, 
    TransitionSteps
)
from uuid import uuid4


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
        self._id = uuid4()
        self._room_name = room_name
        self._scene_name = scene_name
        self._duration = duration if duration is not None else Duration(minutes=7)
        self._brightness_range = (
            brightness_range if brightness_range is not None else BrightnessRange(start=1, end=100)
        )
        self._steps = steps if steps is not None else TransitionSteps(count=70)
        self._easing_function = easing_function if easing_function is not None else (lambda t: t)

        self._status = AlarmStatus.PENDING
        self._current_step = 0
        self._domain_events: list[DomainEvent] = []

    @property
    def id(self) -> UUID:
        return self._id
    
    @property
    def status(self) -> AlarmStatus:
        return self._status

    def collect_events(self) -> list[DomainEvent]:
        events = self._domain_events.copy()
        self._domain_events.clear()
        return events

    def start(self) -> None:
        if not self._can_start():
            raise ValueError(f"Cannot start alarm in status {self._status}")

        self._status = AlarmStatus.RUNNING
        self._raise_event(AlarmStarted(
            aggregate_id=self._id,
            occurred_at=datetime.now(),
            room_name=self._room_name,
            scene_name=self._scene_name
        ))

    def _raise_event(self, event: DomainEvent) -> None:
        self._domain_events.append(event)

    def _can_start(self) -> bool:
        return self._status == AlarmStatus.PENDING

    def progress_step(self) -> None:
        if not self._can_progress():
            raise ValueError(f"Cannot progress alarm in status {self._status}")

        brightness = self._calculate_brightness_for_step(self._current_step)

        self._raise_event(BrightnessChangeRequested(
            aggregate_id=self._id,
            occurred_at=datetime.now(),
            room_name=self._room_name,
            brightness=Brightness(percentage=brightness),
            step_number=self._current_step,
            total_steps=self._steps.count
        ))

        if self._current_step < self._steps.count:
            step_duration = self._duration.seconds / self._steps.count
            self._raise_event(WaitRequested(
                aggregate_id=self._id,
                occurred_at=datetime.now(),
                duration_seconds=step_duration
            ))

        self._current_step += 1

        if self._current_step > self._steps.count:
            self._complete()

    def _can_progress(self) -> bool:
        return self._status == AlarmStatus.RUNNING

    def cancel(self) -> None:
        if not self._can_cancel():
            raise ValueError(f"Cannot cancel alarm in status {self._status}")

        self._status = AlarmStatus.CANCELLED
        self._raise_event(AlarmCancelled(
            aggregate_id=self._id,
            occurred_at=datetime.now(),
            room_name=self._room_name,
            at_step=self._current_step
        ))

    def _can_cancel(self) -> bool:
        return self._status == AlarmStatus.RUNNING

    def _complete(self) -> None:
        self._status = AlarmStatus.COMPLETED
        self._raise_event(AlarmCompleted(
            aggregate_id=self._id,
            occurred_at=datetime.now(),
            room_name=self._room_name,
            total_steps=self._steps.count
        ))

    def _calculate_brightness_for_step(self, step: int) -> int:
        progress = step / self._steps.count
        eased_progress = self._easing_function(progress)
        brightness = self._brightness_range.start + (
            self._brightness_range.range * eased_progress
        )
        return int(brightness)