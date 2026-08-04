from datetime import timedelta
from typing import Self
from uuid import UUID

from pydantic import BaseModel, Field

from huerise.features.alarm.domain import (
    AlarmProfile,
    IntroSettings,
    RingtoneSettings,
    SunriseSettings,
)

_SOUND_ID_DESCRIPTION = (
    "UUID of a sound returned by GET /sounds, "
    "e.g. '5c0806e7-7162-5be7-948e-33d349bde4a8'."
)


class SunriseSchema(BaseModel):
    scene_name: str = Field(
        default="Tageslichtwecker",
        description="Name of a Hue scene from GET /rooms/{room_name}.",
    )
    duration_minutes: int = Field(default=7, ge=0, le=120)
    brightness_start: int = Field(default=1, ge=1, le=99)
    brightness_end: int = Field(default=100, ge=2, le=100)

    def to_domain(self) -> SunriseSettings:
        return SunriseSettings(
            scene_name=self.scene_name,
            duration=timedelta(minutes=self.duration_minutes),
            brightness_start=self.brightness_start,
            brightness_end=self.brightness_end,
        )

    @classmethod
    def from_domain(cls, settings: SunriseSettings) -> Self:
        return cls(
            scene_name=settings.scene_name,
            duration_minutes=settings.duration_minutes,
            brightness_start=settings.brightness_start,
            brightness_end=settings.brightness_end,
        )


class RingtoneSchema(BaseModel):
    sound_id: UUID = Field(description=_SOUND_ID_DESCRIPTION)
    volume: int = Field(default=80, ge=0, le=100)

    def to_domain(self) -> RingtoneSettings:
        return RingtoneSettings(sound_id=self.sound_id, volume=self.volume)

    @classmethod
    def from_domain(cls, settings: RingtoneSettings) -> Self:
        return cls(sound_id=settings.sound_id, volume=settings.volume)


class IntroSchema(BaseModel):
    sound_id: UUID = Field(description=_SOUND_ID_DESCRIPTION)

    def to_domain(self) -> IntroSettings:
        return IntroSettings(sound_id=self.sound_id)

    @classmethod
    def from_domain(cls, settings: IntroSettings) -> Self:
        return cls(sound_id=settings.sound_id)


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
            intro=IntroSchema.from_domain(profile.intro_settings),
            sunrise=SunriseSchema.from_domain(profile.sunrise_settings),
            ringtone=RingtoneSchema.from_domain(profile.ringtone_settings),
        )
