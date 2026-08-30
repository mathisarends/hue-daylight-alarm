from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends

from huerise.authentication import require_api_key
from huerise.features.lighting.application import SceneService
from huerise.features.lighting.presentation.mappers import (
    to_available_scene_response,
    to_room_response,
)
from huerise.features.lighting.presentation.schemas import (
    AvailableSceneResponse,
    RoomResponse,
)

scene_router = APIRouter(
    tags=["lighting"],
    route_class=DishkaRoute,
    dependencies=[Depends(require_api_key)],
)


@scene_router.get(
    "/rooms",
    response_model=list[RoomResponse],
    operation_id="listRooms",
)
async def rooms(
    service: FromDishka[SceneService],
) -> list[RoomResponse]:
    rooms = await service.list_rooms()
    return [to_room_response(room) for room in rooms]


@scene_router.get(
    "/scenes",
    response_model=list[AvailableSceneResponse],
    operation_id="listScenes",
)
async def scenes(
    service: FromDishka[SceneService],
) -> list[AvailableSceneResponse]:
    scenes = await service.list_scenes()
    return [to_available_scene_response(scene) for scene in scenes]
