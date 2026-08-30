from datetime import timedelta
from typing import Self
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from huerise.features.devices.application import DEMO_DURATION, SunriseDemo
from huerise.features.devices.domain import Room, SunriseRamp


class SceneRead(BaseModel):
    id: UUID
    name: str


class RoomRead(BaseModel):
    id: UUID
    name: str
    scenes: list[SceneRead]

    @classmethod
    def from_domain(cls, room: Room) -> Self:
        return cls(
            id=room.id,
            name=room.name,
            scenes=[SceneRead(id=scene.id, name=scene.name) for scene in room.scenes],
        )


class SceneActivationRequest(BaseModel):
    brightness: float | None = Field(default=None, ge=0, le=100)


class SunriseDemoRequest(BaseModel):
    """The sunrise to replay, compressed into a handful of seconds."""

    duration_seconds: float = Field(
        default=DEMO_DURATION.total_seconds(),
        gt=0,
        le=300,
        description="How long the whole climb should take.",
    )
    brightness_start: int = Field(default=1, ge=1, le=100)
    brightness_end: int = Field(default=100, ge=1, le=100)

    @model_validator(mode="after")
    def _check_brightness_climbs(self) -> Self:
        if self.brightness_start >= self.brightness_end:
            raise ValueError("brightness_start must be below brightness_end")
        return self

    def to_ramp(self) -> SunriseRamp:
        return SunriseRamp(
            duration=timedelta(seconds=self.duration_seconds),
            brightness_start=self.brightness_start,
            brightness_end=self.brightness_end,
        )


class SunriseDemoRead(BaseModel):
    """The demo now running, in enough detail for a client to mirror it."""

    room_id: UUID
    room_name: str
    scene_id: UUID
    scene_name: str
    brightness_start: int
    brightness_end: int
    steps: int = Field(description="Brightness changes this demo will send.")
    step_interval_seconds: float
    duration_seconds: float

    @classmethod
    def from_domain(cls, demo: SunriseDemo) -> Self:
        return cls(
            room_id=demo.room.id,
            room_name=demo.room.name,
            scene_id=demo.scene.id,
            scene_name=demo.scene.name,
            brightness_start=demo.ramp.brightness_start,
            brightness_end=demo.ramp.brightness_end,
            steps=demo.steps,
            step_interval_seconds=demo.step_interval.total_seconds(),
            duration_seconds=demo.duration.total_seconds(),
        )
