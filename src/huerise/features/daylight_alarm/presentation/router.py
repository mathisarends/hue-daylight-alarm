from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import Depends, status

from huerise.authentication import require_api_key
from huerise.exception_handlers import ExceptionRouter
from huerise.features.daylight_alarm.application import (
    DaylightAlarm,
    DaylightAlarmConfiguration,
)
from huerise.features.daylight_alarm.presentation.errors import (
    configuration_errors,
    start_alarm_errors,
)
from huerise.features.daylight_alarm.presentation.schemas import (
    AlarmStatusResponse,
    DaylightAlarmConfigurationRequest,
    DaylightAlarmConfigurationResponse,
    StartRequest,
)

router = ExceptionRouter(
    prefix="/daylight-alarm",
    tags=["daylight-alarm"],
    route_class=DishkaRoute,
    dependencies=[Depends(require_api_key)],
)


@router.get(
    "/configuration",
    response_model=DaylightAlarmConfigurationResponse,
    operation_id="getDaylightAlarmConfiguration",
    errors=configuration_errors,
)
async def get_configuration(
    configuration: FromDishka[DaylightAlarmConfiguration],
) -> DaylightAlarmConfigurationResponse:
    return configuration.get()


@router.put(
    "/configuration",
    response_model=DaylightAlarmConfigurationResponse,
    operation_id="setDaylightAlarmConfiguration",
    errors=configuration_errors,
)
async def set_configuration(
    body: DaylightAlarmConfigurationRequest,
    configuration: FromDishka[DaylightAlarmConfiguration],
) -> DaylightAlarmConfigurationResponse:
    after_alarm = body.after_alarm
    return await configuration.save(
        room_id=body.room_id,
        scene_id=body.scene_id,
        duration_seconds=body.duration_seconds,
        after_alarm_room_id=after_alarm.room_id if after_alarm is not None else None,
        after_alarm_scene_id=after_alarm.scene_id if after_alarm is not None else None,
        after_alarm_brightness=(
            after_alarm.brightness if after_alarm is not None else None
        ),
        after_alarm_delay_seconds=(
            after_alarm.delay_seconds if after_alarm is not None else None
        ),
    )


@router.post(
    "/start",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=AlarmStatusResponse,
    operation_id="startDaylightAlarm",
    errors=start_alarm_errors,
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
