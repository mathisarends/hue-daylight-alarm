from typing import Literal, Self
from uuid import UUID

from pydantic import BaseModel, Field

from huerise.features.lighting.application import (
    AvailableScene,
    DiscoveredBridge,
    DoctorReport,
    OnboardingState,
    OnboardingStatus,
    Room,
)


class DoctorCheckResponse(BaseModel):
    name: str
    status: Literal["ok"]


class DoctorResponse(BaseModel):
    status: Literal["ok"]
    checks: list[DoctorCheckResponse]

    @classmethod
    def from_report(cls, report: DoctorReport) -> Self:
        return cls(
            status=report.status,
            checks=[
                DoctorCheckResponse(name=check.name, status=check.status)
                for check in report.checks
            ],
        )


class SceneResponse(BaseModel):
    id: UUID
    name: str


class AvailableSceneResponse(SceneResponse):
    room_id: UUID
    room_name: str

    @classmethod
    def from_domain(cls, scene: AvailableScene) -> Self:
        return cls(
            id=scene.id,
            name=scene.name,
            room_id=scene.room_id,
            room_name=scene.room_name,
        )


class RoomResponse(BaseModel):
    id: UUID
    name: str
    scenes: list[SceneResponse]

    @classmethod
    def from_domain(cls, room: Room) -> Self:
        return cls(
            id=room.id,
            name=room.name,
            scenes=[
                SceneResponse(id=scene.id, name=scene.name) for scene in room.scenes
            ],
        )


class BridgeResponse(BaseModel):
    id: str
    ip_address: str
    selected: bool

    @classmethod
    def from_domain(cls, bridge: DiscoveredBridge) -> Self:
        return cls(
            id=bridge.id,
            ip_address=bridge.ip_address,
            selected=bridge.selected,
        )


class BridgeSelectionRequest(BaseModel):
    bridge_id: str = Field(min_length=1)


class OnboardingStatusResponse(BaseModel):
    state: OnboardingState
    bridge_id: str | None
    ip_address: str | None
    read_only: bool

    @classmethod
    def from_domain(cls, onboarding: OnboardingStatus) -> Self:
        return cls(
            state=onboarding.state,
            bridge_id=onboarding.bridge_id,
            ip_address=onboarding.ip_address,
            read_only=onboarding.read_only,
        )
