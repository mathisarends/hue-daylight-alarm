import uuid
from unittest.mock import AsyncMock, MagicMock

from huerise.features.alarm.domain import (
    Alarm,
    AlarmRepository,
    AlarmStatus,
    AlarmType,
    IntroConfig,
    RingtoneConfig,
    Schedule,
    SunriseConfig,
)


def make_alarm(
    status: AlarmStatus = AlarmStatus.INACTIVE,
    series_id: uuid.UUID | None = None,
    hour: int = 7,
    minute: int = 0,
) -> Alarm:
    return Alarm(
        label="Morning",
        schedule=Schedule(hour=hour, minute=minute),
        status=status,
        alarm_type=AlarmType.ONE_TIME if series_id is None else AlarmType.RECURRING,
        series_id=series_id,
        intro_config=IntroConfig(audio_file="intro.mp3"),
        sunrise_config=SunriseConfig(room_name="Bedroom", steps=1, duration_minutes=0),
        ringtone_config=RingtoneConfig(audio_file="alarm.mp3"),
    )


def make_repo(
    get_return: Alarm | None = None,
    get_all_return: list[Alarm] | None = None,
    get_scheduled_return: list[Alarm] | None = None,
) -> AlarmRepository:
    repo = MagicMock(spec=AlarmRepository)
    repo.get = AsyncMock(return_value=get_return)
    repo.get_all = AsyncMock(return_value=get_all_return or [])
    repo.get_scheduled = AsyncMock(return_value=get_scheduled_return or [])
    repo.save = AsyncMock(side_effect=lambda a: a)
    repo.delete = AsyncMock()
    return repo
