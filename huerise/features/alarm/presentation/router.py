from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, HTTPException

from huerise.features.alarm.application import AlarmProfileService, AlarmService
from huerise.features.alarm.presentation.mapper import (
    to_alarm_out,
    to_occurrence_out,
    to_profile_out,
)
from huerise.features.alarm.presentation.schemas import (
    AlarmOut,
    CreateAlarmBody,
    CreateProfileBody,
    OccurrenceOut,
    ProfileOut,
    SetVolumeBody,
    SnoozeAlarmBody,
)

router = APIRouter(prefix="/alarms", tags=["Alarms"], route_class=DishkaRoute)
profile_router = APIRouter(
    prefix="/alarm-profiles", tags=["Alarm Profiles"], route_class=DishkaRoute
)


def _parse_timezone(name: str) -> ZoneInfo:
    try:
        return ZoneInfo(name)
    except ZoneInfoNotFoundError:
        raise HTTPException(status_code=400, detail=f"Unknown timezone: {name}")


@router.get("", response_model=list[AlarmOut], operation_id="listAlarms")
async def list_alarms(alarm_service: FromDishka[AlarmService]) -> list[AlarmOut]:
    alarms = await alarm_service.list_alarms()
    return [to_alarm_out(alarm) for alarm in alarms]


@router.post("", response_model=AlarmOut, status_code=201, operation_id="createAlarm")
async def create_alarm(
    body: CreateAlarmBody,
    alarm_service: FromDishka[AlarmService],
) -> AlarmOut:
    alarm = await alarm_service.create_alarm(
        label=body.label,
        hour=body.hour,
        minute=body.minute,
        room_name=body.room_name,
        weekdays=frozenset(body.days),
        tz=_parse_timezone(body.timezone),
        profile_id=body.profile_id,
    )
    return to_alarm_out(alarm)


@router.get("/{alarm_id}", response_model=AlarmOut, operation_id="getAlarm")
async def get_alarm(
    alarm_id: UUID,
    alarm_service: FromDishka[AlarmService],
) -> AlarmOut:
    return to_alarm_out(await alarm_service.get_alarm(alarm_id))


@router.post("/{alarm_id}/enable", response_model=AlarmOut, operation_id="enableAlarm")
async def enable_alarm(
    alarm_id: UUID,
    alarm_service: FromDishka[AlarmService],
) -> AlarmOut:
    return to_alarm_out(await alarm_service.enable(alarm_id))


@router.post(
    "/{alarm_id}/disable", response_model=AlarmOut, operation_id="disableAlarm"
)
async def disable_alarm(
    alarm_id: UUID,
    alarm_service: FromDishka[AlarmService],
) -> AlarmOut:
    return to_alarm_out(await alarm_service.disable(alarm_id))


@router.post(
    "/{alarm_id}/snooze", response_model=OccurrenceOut, operation_id="snoozeAlarm"
)
async def snooze_alarm(
    alarm_id: UUID,
    body: SnoozeAlarmBody,
    alarm_service: FromDishka[AlarmService],
) -> OccurrenceOut:
    occurrence = await alarm_service.snooze(alarm_id, minutes=body.minutes)
    return to_occurrence_out(occurrence)


@router.post(
    "/{alarm_id}/dismiss", response_model=OccurrenceOut, operation_id="dismissAlarm"
)
async def dismiss_alarm(
    alarm_id: UUID,
    alarm_service: FromDishka[AlarmService],
) -> OccurrenceOut:
    return to_occurrence_out(await alarm_service.dismiss(alarm_id))


@router.get(
    "/{alarm_id}/occurrences",
    response_model=list[OccurrenceOut],
    operation_id="listOccurrences",
)
async def list_occurrences(
    alarm_id: UUID,
    alarm_service: FromDishka[AlarmService],
    limit: int = 20,
) -> list[OccurrenceOut]:
    occurrences = await alarm_service.list_occurrences(alarm_id, limit=limit)
    return [to_occurrence_out(occurrence) for occurrence in occurrences]


@router.post("/volume", status_code=204, response_model=None, operation_id="setVolume")
async def set_volume(
    body: SetVolumeBody,
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


@profile_router.get("", response_model=list[ProfileOut], operation_id="listProfiles")
async def list_profiles(
    profile_service: FromDishka[AlarmProfileService],
) -> list[ProfileOut]:
    profiles = await profile_service.list_profiles()
    return [to_profile_out(profile) for profile in profiles]


@profile_router.post(
    "", response_model=ProfileOut, status_code=201, operation_id="createProfile"
)
async def create_profile(
    body: CreateProfileBody,
    profile_service: FromDishka[AlarmProfileService],
) -> ProfileOut:
    profile = await profile_service.create_profile(
        name=body.name,
        intro_audio_file=body.intro_audio_file,
        ringtone_audio_file=body.ringtone_audio_file,
        scene_name=body.scene_name,
        sunrise_duration_minutes=body.sunrise_duration_minutes,
        brightness_start=body.brightness_start,
        brightness_end=body.brightness_end,
        ringtone_volume=body.ringtone_volume,
    )
    return to_profile_out(profile)
