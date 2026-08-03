from uuid import UUID

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter

from huerise.features.alarm.application import AlarmProfileService, AlarmService
from huerise.features.alarm.presentation.mappers import (
    alarm_to_read,
    occurrence_to_read,
    profile_to_read,
)
from huerise.features.alarm.presentation.schemas import (
    AlarmCreate,
    AlarmRead,
    OccurrenceRead,
    ProfileCreate,
    ProfileRead,
    SnoozeRequest,
    VolumeRequest,
)

router = APIRouter(prefix="/alarms", tags=["Alarms"], route_class=DishkaRoute)
profile_router = APIRouter(
    prefix="/alarm-profiles", tags=["Alarm Profiles"], route_class=DishkaRoute
)


@router.get("", response_model=list[AlarmRead], operation_id="listAlarms")
async def list_alarms(alarm_service: FromDishka[AlarmService]) -> list[AlarmRead]:
    alarms = await alarm_service.list_alarms()
    return [alarm_to_read(alarm) for alarm in alarms]


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
    return alarm_to_read(alarm)


@router.get("/{alarm_id}", response_model=AlarmRead, operation_id="getAlarm")
async def get_alarm(
    alarm_id: UUID,
    alarm_service: FromDishka[AlarmService],
) -> AlarmRead:
    alarm = await alarm_service.get_alarm(alarm_id)
    return alarm_to_read(alarm)


@router.post("/{alarm_id}/enable", response_model=AlarmRead, operation_id="enableAlarm")
async def enable_alarm(
    alarm_id: UUID,
    alarm_service: FromDishka[AlarmService],
) -> AlarmRead:
    alarm = await alarm_service.enable(alarm_id)
    return alarm_to_read(alarm)


@router.post(
    "/{alarm_id}/disable", response_model=AlarmRead, operation_id="disableAlarm"
)
async def disable_alarm(
    alarm_id: UUID,
    alarm_service: FromDishka[AlarmService],
) -> AlarmRead:
    alarm = await alarm_service.disable(alarm_id)
    return alarm_to_read(alarm)


@router.post(
    "/{alarm_id}/snooze", response_model=OccurrenceRead, operation_id="snoozeAlarm"
)
async def snooze_alarm(
    alarm_id: UUID,
    body: SnoozeRequest,
    alarm_service: FromDishka[AlarmService],
) -> OccurrenceRead:
    occurrence = await alarm_service.snooze(alarm_id, minutes=body.minutes)
    return occurrence_to_read(occurrence)


@router.post(
    "/{alarm_id}/dismiss", response_model=OccurrenceRead, operation_id="dismissAlarm"
)
async def dismiss_alarm(
    alarm_id: UUID,
    alarm_service: FromDishka[AlarmService],
) -> OccurrenceRead:
    occurrence = await alarm_service.dismiss(alarm_id)
    return occurrence_to_read(occurrence)


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
    return [occurrence_to_read(occurrence) for occurrence in occurrences]


@router.post("/volume", status_code=204, response_model=None, operation_id="setVolume")
async def set_volume(
    body: VolumeRequest,
    alarm_service: FromDishka[AlarmService],
) -> None:
    await alarm_service.set_volume(body.volume)


@router.delete(
    "/{alarm_id}", status_code=204, response_model=None, operation_id="deleteAlarm"
)
async def delete_alarm(
    alarm_id: UUID,
    alarm_service: FromDishka[AlarmService],
) -> None:
    await alarm_service.delete(alarm_id)


@profile_router.get("", response_model=list[ProfileRead], operation_id="listProfiles")
async def list_profiles(
    profile_service: FromDishka[AlarmProfileService],
) -> list[ProfileRead]:
    profiles = await profile_service.list_profiles()
    return [profile_to_read(profile) for profile in profiles]


@profile_router.post(
    "", response_model=ProfileRead, status_code=201, operation_id="createProfile"
)
async def create_profile(
    body: ProfileCreate,
    profile_service: FromDishka[AlarmProfileService],
) -> ProfileRead:
    profile = await profile_service.create_profile(
        name=body.name,
        intro_config=body.intro.to_domain(),
        sunrise_config=body.sunrise.to_domain(),
        ringtone_config=body.ringtone.to_domain(),
    )
    return profile_to_read(profile)
