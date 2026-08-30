from typing import Literal, Self
from uuid import UUID

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field

from huerise.authentication import require_api_key
from huerise.features.lighting.doctor import Doctor, DoctorReport
from huerise.features.lighting.hue import Room
from huerise.features.lighting.onboarding import (
    DiscoveredBridge,
    HueOnboarding,
    OnboardingState,
    OnboardingStatus,
)
from huerise.features.lighting.services import SceneService

router = APIRouter(
    route_class=DishkaRoute,
    dependencies=[Depends(require_api_key)],
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


class DemoResponse(BaseModel):
    status: Literal["started"] = "started"
    duration_seconds: Literal[10] = 10


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


@router.get("/doctor", response_model=DoctorResponse, tags=["health"])
async def doctor(service: FromDishka[Doctor]) -> DoctorResponse:
    return DoctorResponse.from_report(await service.check())


@router.get("/rooms", response_model=list[RoomResponse], tags=["lighting"])
async def rooms(service: FromDishka[SceneService]) -> list[RoomResponse]:
    return [RoomResponse.from_domain(room) for room in await service.list_rooms()]


@router.post(
    "/rooms/{room_id}/scenes/{scene_id}/demo",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=DemoResponse,
    tags=["lighting"],
)
async def demo(
    room_id: UUID,
    scene_id: UUID,
    service: FromDishka[SceneService],
) -> DemoResponse:
    await service.demo(room_id, scene_id)
    return DemoResponse()


@router.delete(
    "/rooms/{room_id}/scenes/{scene_id}/demo",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    tags=["lighting"],
)
async def stop_demo(
    room_id: UUID,
    scene_id: UUID,
    service: FromDishka[SceneService],
) -> None:
    await service.stop_demo()


@router.get("/hue/bridges", response_model=list[BridgeResponse], tags=["hue-setup"])
async def discover_bridges(
    service: FromDishka[HueOnboarding],
) -> list[BridgeResponse]:
    return [BridgeResponse.from_domain(item) for item in await service.discover()]


@router.get(
    "/hue/bridge", response_model=OnboardingStatusResponse, tags=["hue-setup"]
)
async def bridge_status(
    service: FromDishka[HueOnboarding],
) -> OnboardingStatusResponse:
    return OnboardingStatusResponse.from_domain(service.status())


@router.put(
    "/hue/bridge", response_model=OnboardingStatusResponse, tags=["hue-setup"]
)
async def select_bridge(
    body: BridgeSelectionRequest,
    service: FromDishka[HueOnboarding],
) -> OnboardingStatusResponse:
    return OnboardingStatusResponse.from_domain(await service.select(body.bridge_id))


@router.post(
    "/hue/bridge/register",
    response_model=OnboardingStatusResponse,
    tags=["hue-setup"],
)
async def register_bridge(
    service: FromDishka[HueOnboarding],
) -> OnboardingStatusResponse:
    return OnboardingStatusResponse.from_domain(await service.register())
