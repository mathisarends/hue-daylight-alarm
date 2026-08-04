from datetime import timedelta
from typing import Self
from uuid import UUID

from pydantic import BaseModel, Field

from huerise.features.alarm.domain import (
    AlarmProfile,
    IntroConfig,
    RingtoneConfig,
    SunriseConfig,
)

_SOUND_ID_DESCRIPTION = (
    "UUID of a sound returned by GET /sounds, "
    "e.g. '5c0806e7-7162-5be7-948e-33d349bde4a8'."
)


class SunriseSchema(BaseModel):
    scene_id: UUID = Field(description="Stable Hue scene UUID returned by GET /rooms.")
    scene_name: str = Field(
        description="Display metadata for the selected Hue scene.",
    )
    duration_minutes: int = Field(default=7, ge=0, le=120)
    brightness_start: int = Field(default=1, ge=1, le=99)
    brightness_end: int = Field(default=100, ge=2, le=100)

    def to_domain(self) -> SunriseConfig:
        return SunriseConfig(
            scene_id=self.scene_id,
            scene_name=self.scene_name,
            duration=timedelta(minutes=self.duration_minutes),
            brightness_start=self.brightness_start,
            brightness_end=self.brightness_end,
        )

    @classmethod
    def from_domain(cls, config: SunriseConfig) -> Self:
        return cls(
            scene_id=config.scene_id,
            scene_name=config.scene_name,
            duration_minutes=config.duration_minutes,
            brightness_start=config.brightness_start,
            brightness_end=config.brightness_end,
        )


class RingtoneSchema(BaseModel):
    sound_id: UUID = Field(description=_SOUND_ID_DESCRIPTION)
    volume: int = Field(default=80, ge=0, le=100)

    def to_domain(self) -> RingtoneConfig:
        return RingtoneConfig(sound_id=self.sound_id, volume=self.volume)

    @classmethod
    def from_domain(cls, config: RingtoneConfig) -> Self:
        return cls(sound_id=config.sound_id, volume=config.volume)


class IntroSchema(BaseModel):
    sound_id: UUID = Field(description=_SOUND_ID_DESCRIPTION)

    def to_domain(self) -> IntroConfig:
        return IntroConfig(sound_id=self.sound_id)

    @classmethod
    def from_domain(cls, config: IntroConfig) -> Self:
        return cls(sound_id=config.sound_id)


class ProfileCreate(BaseModel):
    name: str
    intro: IntroSchema
    ringtone: RingtoneSchema
    sunrise: SunriseSchema


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
