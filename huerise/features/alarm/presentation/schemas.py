"""Wire format for the alarm API.

Two conventions keep this small: nested schemas mirror the domain's value
objects instead of flattening them into prefixed fields, and every schema owns
its own translation to and from the domain, so there is no separate mapper.
"""

from datetime import datetime, timedelta
from typing import Self
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, Field, field_validator
from uuid import UUID

from huerise.features.alarm.domain import (
    Alarm,
    AlarmOccurrence,
    AlarmProfile,
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

    @classmethod
    def from_domain(cls, schedule: Schedule) -> Self:
        return cls(
            hour=schedule.hour,
            minute=schedule.minute,
            timezone=schedule.tz_name,
            days=sorted(schedule.weekdays),
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

    @classmethod
    def from_domain(cls, config: SunriseConfig) -> Self:
        return cls(
            scene_name=config.scene_name,
            duration_minutes=config.duration_minutes,
            brightness_start=config.brightness_start,
            brightness_end=config.brightness_end,
        )


class RingtoneSchema(BaseModel):
    audio_file: str
    volume: int = Field(default=80, ge=0, le=100)

    def to_domain(self) -> RingtoneConfig:
        return RingtoneConfig(audio_file=self.audio_file, volume=self.volume)

    @classmethod
    def from_domain(cls, config: RingtoneConfig) -> Self:
        return cls(audio_file=config.audio_file, volume=config.volume)


class IntroSchema(BaseModel):
    audio_file: str

    def to_domain(self) -> IntroConfig:
        return IntroConfig(audio_file=self.audio_file)

    @classmethod
    def from_domain(cls, config: IntroConfig) -> Self:
        return cls(audio_file=config.audio_file)


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


class ProfileCreate(BaseModel):
    name: str
    intro: IntroSchema
    ringtone: RingtoneSchema
    sunrise: SunriseSchema = SunriseSchema()


class ProfileRead(ProfileCreate):
    """Everything a profile is created with, plus what the server owns."""

    id: UUID
    is_default: bool

    @classmethod
    def from_domain(cls, profile: AlarmProfile) -> Self:
        return cls(
            id=profile.id,
            name=profile.name,
            is_default=profile.is_default,
            intro=IntroSchema.from_domain(profile.intro_config),
            sunrise=SunriseSchema.from_domain(profile.sunrise_config),
            ringtone=RingtoneSchema.from_domain(profile.ringtone_config),
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


class VolumeRequest(BaseModel):
    volume: int = Field(ge=0, le=100)
