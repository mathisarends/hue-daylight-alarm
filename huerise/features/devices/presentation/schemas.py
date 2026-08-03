from typing import Self

from pydantic import BaseModel, Field

from huerise.features.devices.application.sound_service import PREVIEW_VOLUME
from huerise.features.devices.domain import Sound, SoundCategory


class SoundRead(BaseModel):
    """A sound as an alarm profile refers to it."""

    id: str = Field(description="Store this in a profile, e.g. 'wake_up/bowls'.")
    name: str
    category: SoundCategory

    @classmethod
    def from_domain(cls, sound: Sound) -> Self:
        return cls(id=sound.id, name=sound.name, category=sound.category)


class SoundPreviewRequest(BaseModel):
    sound_id: str
    volume: int = Field(default=PREVIEW_VOLUME, ge=0, le=100)


class VolumeRequest(BaseModel):
    volume: int = Field(ge=0, le=100)
