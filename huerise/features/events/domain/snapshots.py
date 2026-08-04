from datetime import datetime
from typing import Self
from uuid import UUID

from pydantic import BaseModel

from huerise.features.alarm.domain import (
    Alarm,
    AlarmOccurrence,
    OccurrenceState,
    Schedule,
    Weekday,
)


class ScheduleSnapshot(BaseModel):
    hour: int
    minute: int
    timezone: str
    weekdays: list[Weekday]

    @classmethod
    def from_domain(cls, schedule: Schedule) -> Self:
        return cls(
            hour=schedule.hour,
            minute=schedule.minute,
            timezone=schedule.tz_name,
            weekdays=sorted(schedule.weekdays),
        )


class AlarmSnapshot(BaseModel):
    """An alarm rule as of the moment an event fired.

    Carries enough to render a row without a follow-up GET, so a display can
    stay in sync from the stream alone.
    """

    id: UUID
    label: str
    schedule: ScheduleSnapshot
    room_name: str
    profile_id: UUID
    is_enabled: bool
    next_occurrence: datetime | None

    @classmethod
    def from_domain(cls, alarm: Alarm) -> Self:
        return cls(
            id=alarm.id,
            label=alarm.label,
            schedule=ScheduleSnapshot.from_domain(alarm.schedule),
            room_name=alarm.room_name,
            profile_id=alarm.profile_id,
            is_enabled=alarm.is_enabled,
            next_occurrence=alarm.next_occurrence(),
        )


class OccurrenceSnapshot(BaseModel):
    """One concrete run of an alarm as of the moment an event fired."""

    id: UUID
    alarm_id: UUID
    scheduled_for: datetime
    state: OccurrenceState
    triggered_at: datetime | None
    finished_at: datetime | None
    snooze_count: int
    failure_reason: str | None

    @classmethod
    def from_domain(cls, occurrence: AlarmOccurrence) -> Self:
        return cls(
            id=occurrence.id,
            alarm_id=occurrence.alarm_id,
            scheduled_for=occurrence.scheduled_for,
            state=occurrence.state,
            triggered_at=occurrence.triggered_at,
            finished_at=occurrence.finished_at,
            snooze_count=occurrence.snooze_count,
            failure_reason=occurrence.failure_reason,
        )
