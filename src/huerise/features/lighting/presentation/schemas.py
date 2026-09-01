from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from huerise.features.lighting.application import OnboardingState


class DoctorCheckResponse(BaseModel):
    name: str
    status: Literal["ok"]


class DoctorResponse(BaseModel):
    status: Literal["ok"]
    checks: list[DoctorCheckResponse]


class SceneResponse(BaseModel):
    id: UUID
    name: str
    brightness: float | None


class RoomResponse(BaseModel):
    id: UUID
    name: str
    scenes: list[SceneResponse]


class BridgeResponse(BaseModel):
    id: str
    ip_address: str
    selected: bool


class BridgeSelectionRequest(BaseModel):
    bridge_id: str = Field(min_length=1)


class OnboardingStatusResponse(BaseModel):
    state: OnboardingState
    bridge_id: str | None
    ip_address: str | None
    read_only: bool
