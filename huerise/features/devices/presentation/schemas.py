from typing import Self
from uuid import UUID

from pydantic import BaseModel, Field

from huerise.features.devices.application.sound_service import PREVIEW_VOLUME
from huerise.features.devices.domain import Room, Sound, SoundCategory


class SoundRead(BaseModel):
    """A sound as an alarm profile refers to it."""

    id: UUID = Field(description="Store this UUID in a profile.")
    name: str
    category: SoundCategory

    @classmethod
    def from_domain(cls, sound: Sound) -> Self:
        return cls(id=sound.id, name=sound.name, category=sound.category)


class SoundPreviewRequest(BaseModel):
    sound_id: UUID
    volume: int = Field(default=PREVIEW_VOLUME, ge=0, le=100)


class VolumeRequest(BaseModel):
    volume: int = Field(ge=0, le=100)


class RoomRead(BaseModel):
    name: str
    scene_names: list[str]

    @classmethod
    def from_domain(cls, room: Room) -> Self:
        return cls(name=room.name, scene_names=list(room.scene_names))
