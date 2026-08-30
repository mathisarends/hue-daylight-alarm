from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import Depends, status

from huerise.authentication import require_api_key
from huerise.configuration import ConfigurationError
from huerise.exception_handlers import ExceptionRouter, error
from huerise.features.daylight_alarm.application import (
    AlarmAlreadyRunningError,
    DaylightAlarm,
)
from huerise.features.daylight_alarm.presentation.schemas import (
    AlarmStatusResponse,
    StartRequest,
)
from huerise.features.lighting.application import (
    HueUnavailableError,
    SceneNotFoundError,
)

router = ExceptionRouter(
    prefix="/daylight-alarm",
    tags=["daylight-alarm"],
    route_class=DishkaRoute,
    dependencies=[Depends(require_api_key)],
)


@router.post(
    "/start",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=AlarmStatusResponse,
    operation_id="startDaylightAlarm",
    errors={
        AlarmAlreadyRunningError: error(
            status.HTTP_409_CONFLICT,
            "A daylight alarm is already running.",
        ),
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
async def start(
    alarm: FromDishka[DaylightAlarm],
    body: StartRequest | None = None,
) -> AlarmStatusResponse:
    duration_seconds = await alarm.start(
        duration_seconds=body.duration_seconds if body is not None else None
    )
    return AlarmStatusResponse(duration_seconds=duration_seconds)


@router.post(
    "/stop",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    operation_id="stopDaylightAlarm",
)
async def stop(alarm: FromDishka[DaylightAlarm]) -> None:
    await alarm.stop()
