from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import Depends, status

from huerise.authentication import require_api_key
from huerise.configuration import ConfigurationError
from huerise.exception_handlers import ExceptionRouter, error
from huerise.features.lighting.application import (
    Doctor,
    HueUnavailableError,
    SceneNotFoundError,
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
        SceneNotFoundError: error(
            status.HTTP_404_NOT_FOUND,
            "The configured Hue scene does not exist.",
        ),
        ConfigurationError: error(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "The YAML configuration is missing or invalid.",
        ),
        HueUnavailableError: error(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "The Hue Bridge is not configured, reachable, or authenticated.",
        ),
    },
)
async def doctor(
    service: FromDishka[Doctor],
) -> DoctorResponse:
    report = await service.check()
    return to_doctor_response(report)
