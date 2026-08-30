from uuid import UUID

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends

from huerise.features.lighting.application import SceneService
from huerise.features.lighting.presentation.schemas import (
    RoomRead,
    SceneActivationRequest,
    SunriseDemoRead,
    SunriseDemoRequest,
)
from huerise.presentation import get_current_user

scene_router = APIRouter(
    prefix="/rooms",
    tags=["scenes"],
    route_class=DishkaRoute,
    dependencies=[Depends(get_current_user)],
)


@scene_router.get("", response_model=list[RoomRead], operation_id="list_rooms")
async def list_rooms(scene_service: FromDishka[SceneService]) -> list[RoomRead]:
    rooms = await scene_service.list_rooms()
    return [RoomRead.from_domain(room) for room in rooms]


@scene_router.get("/{room_id}", response_model=RoomRead, operation_id="get_room")
async def get_room(
    room_id: UUID,
    scene_service: FromDishka[SceneService],
) -> RoomRead:
    return RoomRead.from_domain(await scene_service.get_room(room_id))


@scene_router.post(
    "/{room_id}/scenes/{scene_id}/activate",
    status_code=204,
    response_model=None,
    operation_id="activate_scene",
)
async def activate_scene(
    room_id: UUID,
    scene_id: UUID,
    scene_service: FromDishka[SceneService],
    body: SceneActivationRequest | None = None,
) -> None:
    """Preview a scene the way an alarm would start it."""
    await scene_service.activate_scene(
        room_id,
        scene_id,
        brightness=body.brightness if body is not None else None,
    )


@scene_router.post(
    "/{room_id}/scenes/{scene_id}/demo",
    response_model=SunriseDemoRead,
    status_code=202,
    operation_id="demo_scene",
)
async def demo_scene(
    room_id: UUID,
    scene_id: UUID,
    scene_service: FromDishka[SceneService],
    body: SunriseDemoRequest | None = None,
) -> SunriseDemoRead:
    """Fast-forward a whole sunrise on this scene, lights only.

    Returns as soon as the climb is under way, describing the run so a client
    can follow along. The scene does not have to belong to a saved alarm.
    """
    demo = await scene_service.start_demo(
        room_id, scene_id, (body or SunriseDemoRequest()).to_ramp()
    )
    return SunriseDemoRead.from_domain(demo)


@scene_router.delete(
    "/{room_id}/scenes/{scene_id}/demo",
    status_code=204,
    response_model=None,
    operation_id="stop_scene_demo",
)
async def stop_scene_demo(
    room_id: UUID,
    scene_id: UUID,
    scene_service: FromDishka[SceneService],
) -> None:
    """Cut the running demo short. Only one runs at a time, so this ends it."""
    await scene_service.stop_demo()
