from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends

from huerise.features.devices.application import SceneService
from huerise.features.devices.presentation.schemas import RoomRead
from huerise.presentation import require_access_token

scene_router = APIRouter(
    prefix="/rooms",
    tags=["scenes"],
    route_class=DishkaRoute,
    dependencies=[Depends(require_access_token)],
)


@scene_router.get("", response_model=list[RoomRead], operation_id="list_rooms")
async def list_rooms(scene_service: FromDishka[SceneService]) -> list[RoomRead]:
    rooms = await scene_service.list_rooms()
    return [RoomRead.from_domain(room) for room in rooms]


@scene_router.get("/{room_name}", response_model=RoomRead, operation_id="get_room")
async def get_room(
    room_name: str,
    scene_service: FromDishka[SceneService],
) -> RoomRead:
    return RoomRead.from_domain(await scene_service.get_room(room_name))


@scene_router.post(
    "/{room_name}/scenes/{scene_name}/activate",
    status_code=204,
    response_model=None,
    operation_id="activate_scene",
)
async def activate_scene(
    room_name: str,
    scene_name: str,
    scene_service: FromDishka[SceneService],
) -> None:
    """Preview a scene the way an alarm would start it."""
    await scene_service.activate_scene(room_name, scene_name)
