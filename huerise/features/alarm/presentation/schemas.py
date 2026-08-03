from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from huerise.features.alarm.domain.views import AlarmStatus, AlarmType, Weekday


class CreateOneTimeAlarmBody(BaseModel):
    label: str
    hour: int = Field(ge=0, le=23)
    minute: int = Field(ge=0, le=59)
    room_name: str
    intro_audio_file: str = "wake-up-bowls.mp3"
    ringtone_audio_file: str = "get-up-aurora.mp3"


class CreateRecurringAlarmBody(BaseModel):
    label: str
    hour: int = Field(ge=0, le=23)
    minute: int = Field(ge=0, le=59)
    days: list[Weekday] = Field(min_length=1)
    room_name: str
    intro_audio_file: str = "wake-up-bowls.mp3"
    ringtone_audio_file: str = "get-up-aurora.mp3"


class ScheduleOut(BaseModel):
    hour: int
    minute: int
    recurrence: list[Weekday] | None = None


class AlarmOut(BaseModel):
    id: UUID
    label: str
    schedule: ScheduleOut
    status: AlarmStatus
    alarm_type: AlarmType
    series_id: UUID | None = None
    created_at: datetime


class SnoozeAlarmBody(BaseModel):
    minutes: int = Field(default=10, ge=1, le=60)


class SetVolumeBody(BaseModel):
    volume: int = Field(ge=0, le=100)
