from uuid import UUID

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter

from huerise.application.alarm_service import AlarmService
from huerise.presentation.mapper import to_alarm_out
from huerise.presentation.api.schemas import (
    AlarmOut,
    CreateOneTimeAlarmBody,
    CreateRecurringAlarmBody,
    SetVolumeBody,
    SnoozeAlarmBody,
)

router = APIRouter(prefix="/alarms", tags=["Alarms"], route_class=DishkaRoute)


@router.get("", response_model=list[AlarmOut], operation_id="listAlarms")
async def list_alarms(
    service: FromDishka[AlarmService],
) -> list[AlarmOut]:
    alarms = await service.list_alarms()
    return [to_alarm_out(a) for a in alarms]


@router.post(
    "/one-time",
    response_model=AlarmOut,
    status_code=201,
    operation_id="createOneTimeAlarm",
)
async def create_one_time_alarm(
    body: CreateOneTimeAlarmBody,
    service: FromDishka[AlarmService],
) -> AlarmOut:
    alarm = await service.create_one_time(
        label=body.label,
        hour=body.hour,
        minute=body.minute,
        room_name=body.room_name,
        intro_audio_file=body.intro_audio_file,
        ringtone_audio_file=body.ringtone_audio_file,
    )
    return to_alarm_out(alarm)


@router.post(
    "/recurring",
    response_model=AlarmOut,
    status_code=201,
    operation_id="createRecurringAlarm",
)
async def create_recurring_alarm(
    body: CreateRecurringAlarmBody,
    service: FromDishka[AlarmService],
) -> AlarmOut:
    alarm = await service.create_recurring(
        label=body.label,
        hour=body.hour,
        minute=body.minute,
        days=frozenset(body.days),
        room_name=body.room_name,
        intro_audio_file=body.intro_audio_file,
        ringtone_audio_file=body.ringtone_audio_file,
    )
    return to_alarm_out(alarm)


@router.post(
    "/{alarm_id}/activate", response_model=AlarmOut, operation_id="activateAlarm"
)
async def activate_alarm(
    alarm_id: UUID,
    service: FromDishka[AlarmService],
) -> AlarmOut:
    alarm = await service.activate(alarm_id)
    return to_alarm_out(alarm)


@router.post(
    "/{alarm_id}/deactivate", response_model=AlarmOut, operation_id="deactivateAlarm"
)
async def deactivate_alarm(
    alarm_id: UUID,
    service: FromDishka[AlarmService],
) -> AlarmOut:
    alarm = await service.deactivate(alarm_id)
    return to_alarm_out(alarm)


@router.post("/{alarm_id}/cancel", response_model=AlarmOut, operation_id="cancelAlarm")
async def cancel_alarm(
    alarm_id: UUID,
    service: FromDishka[AlarmService],
) -> AlarmOut:
    alarm = await service.cancel(alarm_id)
    return to_alarm_out(alarm)


@router.post("/{alarm_id}/snooze", response_model=AlarmOut, operation_id="snoozeAlarm")
async def snooze_alarm(
    alarm_id: UUID,
    body: SnoozeAlarmBody,
    service: FromDishka[AlarmService],
) -> AlarmOut:
    alarm = await service.snooze(alarm_id, minutes=body.minutes)
    return to_alarm_out(alarm)


@router.post("/volume", status_code=204, response_model=None, operation_id="setVolume")
async def set_volume(
    body: SetVolumeBody,
    service: FromDishka[AlarmService],
) -> None:
    await service.set_volume(body.volume)


@router.delete(
    "/series/{series_id}",
    status_code=204,
    response_model=None,
    operation_id="deleteSeries",
)
async def delete_series(
    series_id: UUID,
    service: FromDishka[AlarmService],
) -> None:
    await service.delete_series(series_id)


@router.delete(
    "/{alarm_id}", status_code=204, response_model=None, operation_id="deleteAlarm"
)
async def delete_alarm(
    alarm_id: UUID,
    service: FromDishka[AlarmService],
) -> None:
    await service.delete(alarm_id)
