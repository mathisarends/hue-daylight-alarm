from datetime import datetime
from typing import Self
from uuid import UUID

from pydantic import BaseModel, Field

from huerise.features.alarm.domain import (
    Alarm,
    AlarmDefect,
    AlarmOccurrence,
    AlarmProfile,
    OccurrenceState,
    Schedule,
    SunriseConfig,
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
    defect: AlarmDefect | None = Field(
        default=None, description="Why this alarm cannot light its room."
    )

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
            defect=alarm.defect,
        )


class SunriseSnapshot(BaseModel):
    scene_id: UUID
    scene_name: str
    duration_minutes: int
    brightness_start: int
    brightness_end: int

    @classmethod
    def from_domain(cls, sunrise: SunriseConfig) -> Self:
        return cls(
            scene_id=sunrise.scene_id,
            scene_name=sunrise.scene_name,
            duration_minutes=sunrise.duration_minutes,
            brightness_start=sunrise.brightness_start,
            brightness_end=sunrise.brightness_end,
        )


class ProfileSnapshot(BaseModel):
    """The behaviour shared by every alarm using it, as of an event.

    Only the sunrise is carried: the intro and ringtone are sounds this app
    owns, and nothing outside it can move them.
    """

    id: UUID
    name: str
    is_default: bool
    sunrise: SunriseSnapshot

    @classmethod
    def from_domain(cls, profile: AlarmProfile) -> Self:
        return cls(
            id=profile.id,
            name=profile.name,
            is_default=profile.is_default,
            sunrise=SunriseSnapshot.from_domain(profile.sunrise_config),
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
