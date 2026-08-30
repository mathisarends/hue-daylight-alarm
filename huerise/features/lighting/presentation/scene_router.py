from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends

from huerise.authentication import require_api_key
from huerise.features.lighting.application import SceneService
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
async def rooms(service: FromDishka[SceneService]) -> list[RoomResponse]:
    return [RoomResponse.from_domain(room) for room in await service.list_rooms()]


@scene_router.get(
    "/scenes",
    response_model=list[AvailableSceneResponse],
    operation_id="listScenes",
)
async def scenes(
    service: FromDishka[SceneService],
) -> list[AvailableSceneResponse]:
    return [
        AvailableSceneResponse.from_domain(scene)
        for scene in await service.list_scenes()
    ]
