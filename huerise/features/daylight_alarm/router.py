from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends, status
from pydantic import BaseModel

from huerise.authentication import require_api_key
from huerise.features.daylight_alarm.service import DaylightAlarm


class AlarmStatusResponse(BaseModel):
    status: str


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
)
async def start(alarm: FromDishka[DaylightAlarm]) -> AlarmStatusResponse:
    await alarm.start()
    return AlarmStatusResponse(status="started")


@router.post(
    "/stop",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
async def stop(alarm: FromDishka[DaylightAlarm]) -> None:
    await alarm.stop()
