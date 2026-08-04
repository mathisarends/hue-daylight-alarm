from datetime import datetime
from typing import Self
from uuid import UUID

from pydantic import BaseModel, Field

from huerise.features.devices.application import AudioOutputStatus
from huerise.features.devices.application.sound_service import PREVIEW_VOLUME
from huerise.features.devices.domain import AudioOutput, Room, Sound, SoundCategory


class SoundRead(BaseModel):
    """A sound as an alarm profile refers to it."""

    id: UUID = Field(description="Store this UUID in a profile.")
    name: str
    category: SoundCategory
    created_at: datetime

    @classmethod
    def from_domain(cls, sound: Sound) -> Self:
        return cls(
            id=sound.id,
            name=sound.name,
            category=sound.category,
            created_at=sound.created_at,
        )


class SoundPreviewRequest(BaseModel):
    sound_id: UUID
    volume: int = Field(default=PREVIEW_VOLUME, ge=0, le=100)


class VolumeRequest(BaseModel):
    volume: int = Field(ge=0, le=100)


class AudioOutputRead(BaseModel):
    """The device sounds are currently played on."""

    active: AudioOutput
    available: list[AudioOutput]

    @classmethod
    def from_domain(cls, status: AudioOutputStatus) -> Self:
        return cls(active=status.active, available=list(status.available))


class AudioOutputRequest(BaseModel):
    output: AudioOutput = Field(description="The output to play on from now on.")


class RoomRead(BaseModel):
    name: str
    scene_names: list[str]

    @classmethod
    def from_domain(cls, room: Room) -> Self:
        return cls(name=room.name, scene_names=list(room.scene_names))
