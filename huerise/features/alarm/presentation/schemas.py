from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from huerise.features.alarm.domain import OccurrenceState, Weekday


class CreateAlarmBody(BaseModel):
    label: str
    hour: int = Field(ge=0, le=23)
    minute: int = Field(ge=0, le=59)
    room_name: str
    days: list[Weekday] = Field(
        default_factory=list,
        description="Empty means the alarm fires once and then disables itself.",
    )
    timezone: str = Field(
        default="Europe/Berlin",
        description="IANA zone. The alarm keeps its wall-clock time across DST.",
    )
    profile_id: UUID | None = Field(
        default=None, description="Defaults to the default profile."
    )


class ScheduleOut(BaseModel):
    hour: int
    minute: int
    timezone: str
    days: list[Weekday]


class AlarmOut(BaseModel):
    id: UUID
    label: str
    is_enabled: bool
    schedule: ScheduleOut
    room_name: str
    profile_id: UUID
    created_at: datetime
    next_occurrence: datetime | None


class OccurrenceOut(BaseModel):
    id: UUID
    alarm_id: UUID
    scheduled_for: datetime
    state: OccurrenceState
    triggered_at: datetime | None
    finished_at: datetime | None
    snooze_count: int
    failure_reason: str | None


class CreateProfileBody(BaseModel):
    name: str
    intro_audio_file: str
    ringtone_audio_file: str
    scene_name: str = "Tageslichtwecker"
    sunrise_duration_minutes: int = Field(default=7, ge=0, le=120)
    brightness_start: int = Field(default=1, ge=1, le=99)
    brightness_end: int = Field(default=100, ge=2, le=100)
    ringtone_volume: int = Field(default=80, ge=0, le=100)


class ProfileOut(BaseModel):
    id: UUID
    name: str
    is_default: bool
    intro_audio_file: str
    scene_name: str
    sunrise_duration_minutes: int
    brightness_start: int
    brightness_end: int
    ringtone_audio_file: str
    ringtone_volume: int


class SnoozeAlarmBody(BaseModel):
    minutes: int = Field(default=10, ge=1, le=60)


class SetVolumeBody(BaseModel):
    volume: int = Field(ge=0, le=100)
