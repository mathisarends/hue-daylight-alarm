from uuid import UUID

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter

from huerise.features.alarm.application import AlarmService
from huerise.features.alarm.presentation.schemas import (
    AlarmCreate,
    AlarmRead,
    OccurrenceRead,
    SnoozeRequest,
)

router = APIRouter(prefix="/alarms", tags=["Alarms"], route_class=DishkaRoute)


@router.get("", response_model=list[AlarmRead], operation_id="listAlarms")
async def list_alarms(alarm_service: FromDishka[AlarmService]) -> list[AlarmRead]:
    alarms = await alarm_service.list_alarms()
    return [AlarmRead.from_domain(alarm) for alarm in alarms]


@router.post("", response_model=AlarmRead, status_code=201, operation_id="create_alarm")
async def create_alarm(
    body: AlarmCreate,
    alarm_service: FromDishka[AlarmService],
) -> AlarmRead:
    alarm = await alarm_service.create_alarm(
        label=body.label,
        schedule=body.schedule.to_domain(),
        room_name=body.room_name,
        profile_id=body.profile_id,
    )
    return AlarmRead.from_domain(alarm)


@router.get("/{alarm_id}", response_model=AlarmRead, operation_id="getAlarm")
async def get_alarm(
    alarm_id: UUID,
    alarm_service: FromDishka[AlarmService],
) -> AlarmRead:
    alarm = await alarm_service.get_alarm(alarm_id)
    return AlarmRead.from_domain(alarm)


@router.post("/{alarm_id}/enable", response_model=AlarmRead, operation_id="enableAlarm")
async def enable_alarm(
    alarm_id: UUID,
    alarm_service: FromDishka[AlarmService],
) -> AlarmRead:
    alarm = await alarm_service.enable(alarm_id)
    return AlarmRead.from_domain(alarm)


@router.post(
    "/{alarm_id}/disable", response_model=AlarmRead, operation_id="disableAlarm"
)
async def disable_alarm(
    alarm_id: UUID,
    alarm_service: FromDishka[AlarmService],
) -> AlarmRead:
    alarm = await alarm_service.disable(alarm_id)
    return AlarmRead.from_domain(alarm)


@router.post(
    "/{alarm_id}/snooze", response_model=OccurrenceRead, operation_id="snoozeAlarm"
)
async def snooze_alarm(
    alarm_id: UUID,
    body: SnoozeRequest,
    alarm_service: FromDishka[AlarmService],
) -> OccurrenceRead:
    occurrence = await alarm_service.snooze(alarm_id, minutes=body.minutes)
    return OccurrenceRead.from_domain(occurrence)


@router.post(
    "/{alarm_id}/dismiss", response_model=OccurrenceRead, operation_id="dismissAlarm"
)
async def dismiss_alarm(
    alarm_id: UUID,
    alarm_service: FromDishka[AlarmService],
) -> OccurrenceRead:
    return OccurrenceRead.from_domain(await alarm_service.dismiss(alarm_id))


@router.get(
    "/{alarm_id}/occurrences",
    response_model=list[OccurrenceRead],
    operation_id="listOccurrences",
)
async def list_occurrences(
    alarm_id: UUID,
    alarm_service: FromDishka[AlarmService],
    limit: int = 20,
) -> list[OccurrenceRead]:
    occurrences = await alarm_service.list_occurrences(alarm_id, limit=limit)
    return [OccurrenceRead.from_domain(occurrence) for occurrence in occurrences]


@router.delete(
    "/{alarm_id}", status_code=204, response_model=None, operation_id="deleteAlarm"
)
async def delete_alarm(
    alarm_id: UUID,
    alarm_service: FromDishka[AlarmService],
) -> None:
    await alarm_service.delete(alarm_id)
