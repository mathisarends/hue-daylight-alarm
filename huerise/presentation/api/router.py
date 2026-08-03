from uuid import UUID

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter

from huerise.application.commands import (
    ActivateAlarmCommand,
    ActivateAlarmCommandHandler,
    CancelAlarmCommand,
    CancelAlarmCommandHandler,
    CreateOneTimeAlarmCommand,
    CreateOneTimeAlarmCommandHandler,
    CreateRecurringAlarmCommand,
    CreateRecurringAlarmCommandHandler,
    DeactivateAlarmCommand,
    DeactivateAlarmCommandHandler,
    DeleteAlarmCommand,
    DeleteAlarmCommandHandler,
    DeleteSeriesCommand,
    DeleteSeriesCommandHandler,
    SetVolumeCommand,
    SetVolumeCommandHandler,
    SnoozeAlarmCommand,
    SnoozeAlarmCommandHandler,
)
from huerise.application.queries import ListAlarmsQuery, ListAlarmsQueryHandler
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
    handler: FromDishka[ListAlarmsQueryHandler],
) -> list[AlarmOut]:
    query = ListAlarmsQuery()
    alarms = await handler.execute(query)
    return [to_alarm_out(a) for a in alarms]


@router.post(
    "/one-time",
    response_model=AlarmOut,
    status_code=201,
    operation_id="createOneTimeAlarm",
)
async def create_one_time_alarm(
    body: CreateOneTimeAlarmBody,
    handler: FromDishka[CreateOneTimeAlarmCommandHandler],
) -> AlarmOut:
    command = CreateOneTimeAlarmCommand(
        label=body.label,
        hour=body.hour,
        minute=body.minute,
        room_name=body.room_name,
        intro_audio_file=body.intro_audio_file,
        ringtone_audio_file=body.ringtone_audio_file,
    )
    alarm = await handler.execute(command)
    return to_alarm_out(alarm)


@router.post(
    "/recurring",
    response_model=AlarmOut,
    status_code=201,
    operation_id="createRecurringAlarm",
)
async def create_recurring_alarm(
    body: CreateRecurringAlarmBody,
    handler: FromDishka[CreateRecurringAlarmCommandHandler],
) -> AlarmOut:
    command = CreateRecurringAlarmCommand(
        label=body.label,
        hour=body.hour,
        minute=body.minute,
        days=frozenset(body.days),
        room_name=body.room_name,
        intro_audio_file=body.intro_audio_file,
        ringtone_audio_file=body.ringtone_audio_file,
    )
    alarm = await handler.execute(command)
    return to_alarm_out(alarm)


@router.post(
    "/{alarm_id}/activate", response_model=AlarmOut, operation_id="activateAlarm"
)
async def activate_alarm(
    alarm_id: UUID,
    handler: FromDishka[ActivateAlarmCommandHandler],
) -> AlarmOut:
    command = ActivateAlarmCommand(alarm_id=alarm_id)
    alarm = await handler.execute(command)
    return to_alarm_out(alarm)


@router.post(
    "/{alarm_id}/deactivate", response_model=AlarmOut, operation_id="deactivateAlarm"
)
async def deactivate_alarm(
    alarm_id: UUID,
    handler: FromDishka[DeactivateAlarmCommandHandler],
) -> AlarmOut:
    command = DeactivateAlarmCommand(alarm_id=alarm_id)
    alarm = await handler.execute(command)
    return to_alarm_out(alarm)


@router.post("/{alarm_id}/cancel", response_model=AlarmOut, operation_id="cancelAlarm")
async def cancel_alarm(
    alarm_id: UUID,
    handler: FromDishka[CancelAlarmCommandHandler],
) -> AlarmOut:
    command = CancelAlarmCommand(alarm_id=alarm_id)
    alarm = await handler.execute(command)
    return to_alarm_out(alarm)


@router.post("/{alarm_id}/snooze", response_model=AlarmOut, operation_id="snoozeAlarm")
async def snooze_alarm(
    alarm_id: UUID,
    body: SnoozeAlarmBody,
    handler: FromDishka[SnoozeAlarmCommandHandler],
) -> AlarmOut:
    command = SnoozeAlarmCommand(alarm_id=alarm_id, minutes=body.minutes)
    alarm = await handler.execute(command)
    return to_alarm_out(alarm)


@router.post("/volume", status_code=204, response_model=None, operation_id="setVolume")
async def set_volume(
    body: SetVolumeBody,
    handler: FromDishka[SetVolumeCommandHandler],
) -> None:
    command = SetVolumeCommand(volume=body.volume)
    await handler.execute(command)


@router.delete(
    "/series/{series_id}",
    status_code=204,
    response_model=None,
    operation_id="deleteSeries",
)
async def delete_series(
    series_id: UUID,
    handler: FromDishka[DeleteSeriesCommandHandler],
) -> None:
    command = DeleteSeriesCommand(series_id=series_id)
    await handler.execute(command)


@router.delete(
    "/{alarm_id}", status_code=204, response_model=None, operation_id="deleteAlarm"
)
async def delete_alarm(
    alarm_id: UUID,
    handler: FromDishka[DeleteAlarmCommandHandler],
) -> None:
    command = DeleteAlarmCommand(alarm_id=alarm_id)
    await handler.execute(command)
