from datetime import datetime, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, Field, field_validator
from uuid import UUID

from huerise.features.alarm.domain import (
    IntroConfig,
    OccurrenceState,
    RingtoneConfig,
    Schedule,
    SunriseConfig,
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
        except ZoneInfoNotFoundError:
            raise ValueError(f"Unknown timezone: {value}")
        return value

    def to_domain(self) -> Schedule:
        return Schedule(
            hour=self.hour,
            minute=self.minute,
            tz=ZoneInfo(self.timezone),
            weekdays=frozenset(self.days),
        )


class SunriseSchema(BaseModel):
    scene_name: str = "Tageslichtwecker"
    duration_minutes: int = Field(default=7, ge=0, le=120)
    brightness_start: int = Field(default=1, ge=1, le=99)
    brightness_end: int = Field(default=100, ge=2, le=100)

    def to_domain(self) -> SunriseConfig:
        return SunriseConfig(
            scene_name=self.scene_name,
            duration=timedelta(minutes=self.duration_minutes),
            brightness_start=self.brightness_start,
            brightness_end=self.brightness_end,
        )


class RingtoneSchema(BaseModel):
    audio_file: str
    volume: int = Field(default=80, ge=0, le=100)

    def to_domain(self) -> RingtoneConfig:
        return RingtoneConfig(audio_file=self.audio_file, volume=self.volume)


class IntroSchema(BaseModel):
    audio_file: str

    def to_domain(self) -> IntroConfig:
        return IntroConfig(audio_file=self.audio_file)


class AlarmCreate(BaseModel):
    label: str
    schedule: ScheduleSchema
    room_name: str
    profile_id: UUID | None = Field(
        default=None, description="Defaults to the default profile."
    )


class AlarmRead(BaseModel):
    id: UUID
    label: str
    schedule: ScheduleSchema
    room_name: str
    profile_id: UUID
    is_enabled: bool
    created_at: datetime
    next_occurrence: datetime | None


class ProfileCreate(BaseModel):
    name: str
    intro: IntroSchema
    ringtone: RingtoneSchema
    sunrise: SunriseSchema = SunriseSchema()


class ProfileRead(ProfileCreate):
    """Everything a profile is created with, plus what the server owns."""

    id: UUID
    is_default: bool


class OccurrenceRead(BaseModel):
    id: UUID
    alarm_id: UUID
    scheduled_for: datetime
    state: OccurrenceState
    triggered_at: datetime | None
    finished_at: datetime | None
    snooze_count: int
    failure_reason: str | None


class SnoozeRequest(BaseModel):
    minutes: int = Field(default=10, ge=1, le=60)


class VolumeRequest(BaseModel):
    volume: int = Field(ge=0, le=100)
