from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends, status

from huerise.authentication import require_api_key
from huerise.features.daylight_alarm.application import DaylightAlarm
from huerise.features.daylight_alarm.presentation.schemas import (
    AlarmStatusResponse,
    StartRequest,
)

router = APIRouter(
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
