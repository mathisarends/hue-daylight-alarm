from datetime import datetime
from typing import Self
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, Field, field_validator

from huerise.features.alarm.domain import (
    Alarm,
    AlarmOccurrence,
    OccurrenceState,
    Schedule,
    Weekday,
)


class ScheduleSchema(BaseModel):
    """When an alarm fires, as wall-clock time in a named zone."""

    hour: int = Field(ge=0, le=23)
    minute: int = Field(ge=0, le=59)
    timezone: str = Field(
        default="Europe/Berlin",
        description="IANA zone. The alarm keeps its wall-clock time across DST.",
    )
    days: list[Weekday] = Field(
        default_factory=list,
        description="Empty means the alarm fires once, then disables itself.",
    )

    @field_validator("timezone")
    @classmethod
    def _known_timezone(cls, value: str) -> str:
        try:
            ZoneInfo(value)
        except ZoneInfoNotFoundError as err:
            raise ValueError(f"Unknown timezone: {value}") from err
        return value

    def to_domain(self) -> Schedule:
        return Schedule(
            hour=self.hour,
            minute=self.minute,
            tz=ZoneInfo(self.timezone),
            weekdays=frozenset(self.days),
        )

    @classmethod
    def from_domain(cls, schedule: Schedule) -> Self:
        return cls(
            hour=schedule.hour,
            minute=schedule.minute,
            timezone=schedule.tz_name,
            days=sorted(schedule.weekdays),
        )


class AlarmCreate(BaseModel):
    label: str
    schedule: ScheduleSchema
    room_name: str
    profile_id: UUID | None = Field(
        default=None, description="Defaults to the default profile."
    )


class AlarmUpdate(BaseModel):
    """A partial change. Omitted fields keep their current value."""

    label: str | None = None
    schedule: ScheduleSchema | None = None
    room_name: str | None = None
    profile_id: UUID | None = None


class AlarmRead(BaseModel):
    id: UUID
    label: str
    schedule: ScheduleSchema
    room_name: str
    profile_id: UUID
    is_enabled: bool
    created_at: datetime
    next_occurrence: datetime | None

    @classmethod
    def from_domain(cls, alarm: Alarm) -> Self:
        return cls(
            id=alarm.id,
            label=alarm.label,
            schedule=ScheduleSchema.from_domain(alarm.schedule),
            room_name=alarm.room_name,
            profile_id=alarm.profile_id,
            is_enabled=alarm.is_enabled,
            created_at=alarm.created_at,
            next_occurrence=alarm.next_occurrence(),
        )


class OccurrenceRead(BaseModel):
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


class SnoozeRequest(BaseModel):
    minutes: int = Field(default=10, ge=1, le=60)
