from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import Depends

from huerise.authentication import require_api_key
from huerise.exception_handlers import ExceptionRouter
from huerise.features.lighting.application import SceneService
from huerise.features.lighting.presentation.errors import scene_errors
from huerise.features.lighting.presentation.mappers import to_available_scene_response
from huerise.features.lighting.presentation.schemas import AvailableSceneResponse

scene_router = ExceptionRouter(
    tags=["lighting"],
    route_class=DishkaRoute,
    dependencies=[Depends(require_api_key)],
)


@scene_router.get(
    "/scenes",
    response_model=list[AvailableSceneResponse],
    operation_id="listScenes",
    errors=scene_errors,
)
async def scenes(
    service: FromDishka[SceneService],
) -> list[AvailableSceneResponse]:
    scenes = await service.list_scenes()
    return [to_available_scene_response(scene) for scene in scenes]
