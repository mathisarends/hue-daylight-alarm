from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import Depends

from huerise.authentication import require_api_key
from huerise.configuration import ConfigurationError
from huerise.exception_handlers import ExceptionRouter
from huerise.features.lighting.application import (
    Doctor,
    HueUnavailableError,
    SceneNotFoundError,
)
from huerise.features.lighting.presentation.errors import (
    configured_scene_not_found,
    invalid_yaml_configuration,
    unavailable_hue_bridge,
)
from huerise.features.lighting.presentation.mappers import to_doctor_response
from huerise.features.lighting.presentation.schemas import DoctorResponse

doctor_router = ExceptionRouter(
    tags=["doctor"],
    route_class=DishkaRoute,
    dependencies=[Depends(require_api_key)],
)


@doctor_router.get(
    "/doctor",
    response_model=DoctorResponse,
    operation_id="doctor",
    errors={
        SceneNotFoundError: configured_scene_not_found,
        ConfigurationError: invalid_yaml_configuration,
        HueUnavailableError: unavailable_hue_bridge,
    },
)
async def doctor(
    service: FromDishka[Doctor],
) -> DoctorResponse:
    report = await service.check()
    return to_doctor_response(report)
