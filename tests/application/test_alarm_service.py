import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from huerise.features.alarm.application import AlarmService
from huerise.features.alarm.domain import (
    AlarmNotFoundError,
    AlarmNotRunningError,
    AlarmStatus,
    AlarmType,
    Weekday,
)
from huerise.features.runner.application import AudioPlayer
from tests.application.conftest import make_alarm, make_repo


def make_audio() -> AudioPlayer:
    audio = MagicMock(spec=AudioPlayer)
    audio.play = AsyncMock()
    audio.stop = AsyncMock()
    audio.set_volume = AsyncMock()
    return audio


def make_alarm_service(repo=None, audio=None) -> AlarmService:
    return AlarmService(
        alarm_repository=repo if repo is not None else make_repo(),
        audio=audio if audio is not None else make_audio(),
    )


class TestAlarmServiceActivate:
    async def test_returns_the_alarm(self) -> None:
        alarm = make_alarm(status=AlarmStatus.INACTIVE)
        alarm_service = make_alarm_service(repo=make_repo(get_return=alarm))

        result = await alarm_service.activate(alarm.id)

        assert result is alarm

    async def test_sets_status_to_scheduled(self) -> None:
        alarm = make_alarm(status=AlarmStatus.INACTIVE)
        alarm_service = make_alarm_service(repo=make_repo(get_return=alarm))

        await alarm_service.activate(alarm.id)

        assert alarm.status == AlarmStatus.SCHEDULED

    async def test_saves_alarm_after_activation(self) -> None:
        alarm = make_alarm(status=AlarmStatus.INACTIVE)
        repo = make_repo(get_return=alarm)
        alarm_service = make_alarm_service(repo=repo)

        await alarm_service.activate(alarm.id)

        repo.save.assert_awaited_once_with(alarm)

    async def test_raises_when_alarm_not_found(self) -> None:
        alarm_service = make_alarm_service(repo=make_repo(get_return=None))

        with pytest.raises(AlarmNotFoundError):
            await alarm_service.activate(uuid.uuid4())


class TestAlarmServiceCancel:
    async def test_returns_the_alarm(self) -> None:
        alarm = make_alarm(status=AlarmStatus.SCHEDULED)
        alarm_service = make_alarm_service(repo=make_repo(get_return=alarm))

        result = await alarm_service.cancel(alarm.id)

        assert result is alarm

    async def test_sets_status_to_cancelled(self) -> None:
        alarm = make_alarm(status=AlarmStatus.SCHEDULED)
        alarm_service = make_alarm_service(repo=make_repo(get_return=alarm))

        await alarm_service.cancel(alarm.id)

        assert alarm.status == AlarmStatus.CANCELLED

    async def test_saves_alarm_after_cancellation(self) -> None:
        alarm = make_alarm(status=AlarmStatus.SCHEDULED)
        repo = make_repo(get_return=alarm)
        alarm_service = make_alarm_service(repo=repo)

        await alarm_service.cancel(alarm.id)

        repo.save.assert_awaited_once_with(alarm)

    async def test_raises_when_alarm_not_found(self) -> None:
        alarm_service = make_alarm_service(repo=make_repo(get_return=None))

        with pytest.raises(AlarmNotFoundError):
            await alarm_service.cancel(uuid.uuid4())


class TestAlarmServiceCreateOneTime:
    async def test_returns_created_alarm(self) -> None:
        alarm_service = make_alarm_service()

        result = await alarm_service.create_one_time(
            label="Sun", hour=7, minute=30, room_name="Bedroom"
        )

        assert result is not None
        assert result.label == "Sun"

    async def test_alarm_has_correct_schedule(self) -> None:
        alarm_service = make_alarm_service()

        result = await alarm_service.create_one_time(
            label="Sun", hour=6, minute=45, room_name="Bedroom"
        )

        assert result.schedule.hour == 6
        assert result.schedule.minute == 45

    async def test_alarm_type_is_one_time(self) -> None:
        alarm_service = make_alarm_service()

        result = await alarm_service.create_one_time(
            label="Sun", hour=7, minute=0, room_name="Bedroom"
        )

        assert result.alarm_type == AlarmType.ONE_TIME

    async def test_alarm_is_scheduled_on_creation(self) -> None:
        alarm_service = make_alarm_service()

        result = await alarm_service.create_one_time(
            label="Sun", hour=7, minute=0, room_name="Bedroom"
        )

        assert result.status == AlarmStatus.SCHEDULED

    async def test_saves_alarm_to_repository(self) -> None:
        repo = make_repo()
        alarm_service = make_alarm_service(repo=repo)

        result = await alarm_service.create_one_time(
            label="Sun", hour=7, minute=0, room_name="Bedroom"
        )

        repo.save.assert_awaited_once_with(result)

    async def test_uses_default_audio_files(self) -> None:
        alarm_service = make_alarm_service()

        result = await alarm_service.create_one_time(
            label="Sun", hour=7, minute=0, room_name="Bedroom"
        )

        assert result.intro_config.audio_file == "wake-up-bowls.mp3"
        assert result.ringtone_config.audio_file == "get-up-aurora.mp3"

    async def test_uses_custom_audio_files_when_provided(self) -> None:
        alarm_service = make_alarm_service()

        result = await alarm_service.create_one_time(
            label="Sun",
            hour=7,
            minute=0,
            room_name="Bedroom",
            intro_audio_file="custom-intro.mp3",
            ringtone_audio_file="custom-ringtone.mp3",
        )

        assert result.intro_config.audio_file == "custom-intro.mp3"
        assert result.ringtone_config.audio_file == "custom-ringtone.mp3"


class TestAlarmServiceCreateRecurring:
    async def test_returns_created_alarm(self) -> None:
        alarm_service = make_alarm_service()

        result = await alarm_service.create_recurring(
            label="Weekday",
            hour=7,
            minute=0,
            days=frozenset({Weekday.MON, Weekday.FRI}),
            room_name="Bedroom",
        )

        assert result is not None
        assert result.label == "Weekday"

    async def test_alarm_type_is_recurring(self) -> None:
        alarm_service = make_alarm_service()

        result = await alarm_service.create_recurring(
            label="Weekday",
            hour=7,
            minute=0,
            days=frozenset({Weekday.MON}),
            room_name="Bedroom",
        )

        assert result.alarm_type == AlarmType.RECURRING

    async def test_alarm_has_correct_days(self) -> None:
        alarm_service = make_alarm_service()

        result = await alarm_service.create_recurring(
            label="Weekday",
            hour=7,
            minute=0,
            days=frozenset({Weekday.MON, Weekday.WED, Weekday.FRI}),
            room_name="Bedroom",
        )

        assert result.schedule.recurrence == frozenset(
            {Weekday.MON, Weekday.WED, Weekday.FRI}
        )

    async def test_alarm_has_series_id_assigned(self) -> None:
        alarm_service = make_alarm_service()

        result = await alarm_service.create_recurring(
            label="Weekday",
            hour=7,
            minute=0,
            days=frozenset({Weekday.MON}),
            room_name="Bedroom",
        )

        assert result.series_id is not None

    async def test_alarm_is_scheduled_on_creation(self) -> None:
        alarm_service = make_alarm_service()

        result = await alarm_service.create_recurring(
            label="Weekday",
            hour=7,
            minute=0,
            days=frozenset({Weekday.MON}),
            room_name="Bedroom",
        )

        assert result.status == AlarmStatus.SCHEDULED

    async def test_saves_alarm_to_repository(self) -> None:
        repo = make_repo()
        alarm_service = make_alarm_service(repo=repo)

        result = await alarm_service.create_recurring(
            label="Weekday",
            hour=7,
            minute=0,
            days=frozenset({Weekday.MON}),
            room_name="Bedroom",
        )

        repo.save.assert_awaited_once_with(result)


class TestAlarmServiceDeactivate:
    async def test_returns_the_alarm(self) -> None:
        alarm = make_alarm(status=AlarmStatus.SCHEDULED)
        alarm_service = make_alarm_service(repo=make_repo(get_return=alarm))

        result = await alarm_service.deactivate(alarm.id)

        assert result is alarm

    async def test_sets_status_to_inactive(self) -> None:
        alarm = make_alarm(status=AlarmStatus.SCHEDULED)
        alarm_service = make_alarm_service(repo=make_repo(get_return=alarm))

        await alarm_service.deactivate(alarm.id)

        assert alarm.status == AlarmStatus.INACTIVE

    async def test_saves_alarm_after_deactivation(self) -> None:
        alarm = make_alarm(status=AlarmStatus.SCHEDULED)
        repo = make_repo(get_return=alarm)
        alarm_service = make_alarm_service(repo=repo)

        await alarm_service.deactivate(alarm.id)

        repo.save.assert_awaited_once_with(alarm)

    async def test_raises_when_alarm_not_found(self) -> None:
        alarm_service = make_alarm_service(repo=make_repo(get_return=None))

        with pytest.raises(AlarmNotFoundError):
            await alarm_service.deactivate(uuid.uuid4())


class TestAlarmServiceDelete:
    async def test_deletes_existing_alarm(self) -> None:
        alarm = make_alarm(status=AlarmStatus.SCHEDULED)
        repo = make_repo(get_return=alarm)
        alarm_service = make_alarm_service(repo=repo)

        await alarm_service.delete(alarm.id)

        repo.delete.assert_awaited_once_with(alarm.id)

    async def test_returns_none(self) -> None:
        alarm = make_alarm(status=AlarmStatus.SCHEDULED)
        repo = make_repo(get_return=alarm)
        alarm_service = make_alarm_service(repo=repo)

        result = await alarm_service.delete(alarm.id)

        assert result is None

    async def test_raises_when_alarm_not_found(self) -> None:
        alarm_service = make_alarm_service(repo=make_repo(get_return=None))

        with pytest.raises(AlarmNotFoundError):
            await alarm_service.delete(uuid.uuid4())

    async def test_does_not_delete_when_not_found(self) -> None:
        repo = make_repo(get_return=None)
        alarm_service = make_alarm_service(repo=repo)

        with pytest.raises(AlarmNotFoundError):
            await alarm_service.delete(uuid.uuid4())

        repo.delete.assert_not_awaited()


class TestAlarmServiceDeleteSeries:
    async def test_deletes_all_alarms_in_series(self) -> None:
        series_id = uuid.uuid4()
        alarm_a = make_alarm(status=AlarmStatus.SCHEDULED, series_id=series_id)
        alarm_b = make_alarm(status=AlarmStatus.SCHEDULED, series_id=series_id)
        repo = make_repo(get_all_return=[alarm_a, alarm_b])
        alarm_service = make_alarm_service(repo=repo)

        await alarm_service.delete_series(series_id)

        assert repo.delete.await_count == 2
        repo.delete.assert_any_await(alarm_a.id)
        repo.delete.assert_any_await(alarm_b.id)

    async def test_does_not_delete_alarms_from_other_series(self) -> None:
        series_id = uuid.uuid4()
        other_series_id = uuid.uuid4()
        alarm_in_series = make_alarm(status=AlarmStatus.SCHEDULED, series_id=series_id)
        alarm_other = make_alarm(
            status=AlarmStatus.SCHEDULED, series_id=other_series_id
        )
        repo = make_repo(get_all_return=[alarm_in_series, alarm_other])
        alarm_service = make_alarm_service(repo=repo)

        await alarm_service.delete_series(series_id)

        repo.delete.assert_awaited_once_with(alarm_in_series.id)

    async def test_does_nothing_when_series_has_no_alarms(self) -> None:
        series_id = uuid.uuid4()
        repo = make_repo(get_all_return=[])
        alarm_service = make_alarm_service(repo=repo)

        await alarm_service.delete_series(series_id)

        repo.delete.assert_not_awaited()


class TestAlarmServiceSetVolume:
    async def test_calls_set_volume_with_given_volume(self) -> None:
        audio = make_audio()
        alarm_service = make_alarm_service(audio=audio)

        await alarm_service.set_volume(75)

        audio.set_volume.assert_awaited_once_with(75)

    async def test_calls_set_volume_with_zero(self) -> None:
        audio = make_audio()
        alarm_service = make_alarm_service(audio=audio)

        await alarm_service.set_volume(0)

        audio.set_volume.assert_awaited_once_with(0)

    async def test_calls_set_volume_with_max(self) -> None:
        audio = make_audio()
        alarm_service = make_alarm_service(audio=audio)

        await alarm_service.set_volume(100)

        audio.set_volume.assert_awaited_once_with(100)


class TestAlarmServiceSnooze:
    async def test_returns_the_alarm(self) -> None:
        alarm = make_alarm(status=AlarmStatus.RINGING)
        alarm_service = make_alarm_service(repo=make_repo(get_return=alarm))

        result = await alarm_service.snooze(alarm.id)

        assert result is alarm

    async def test_sets_status_to_scheduled(self) -> None:
        alarm = make_alarm(status=AlarmStatus.RINGING)
        alarm_service = make_alarm_service(repo=make_repo(get_return=alarm))

        await alarm_service.snooze(alarm.id)

        assert alarm.status == AlarmStatus.SCHEDULED

    async def test_stops_audio(self) -> None:
        alarm = make_alarm(status=AlarmStatus.RINGING)
        audio = make_audio()
        alarm_service = make_alarm_service(
            repo=make_repo(get_return=alarm), audio=audio
        )

        await alarm_service.snooze(alarm.id)

        audio.stop.assert_awaited_once()

    async def test_saves_alarm_after_snooze(self) -> None:
        alarm = make_alarm(status=AlarmStatus.RINGING)
        repo = make_repo(get_return=alarm)
        alarm_service = make_alarm_service(repo=repo)

        await alarm_service.snooze(alarm.id)

        repo.save.assert_awaited_once_with(alarm)

    async def test_raises_when_alarm_not_found(self) -> None:
        alarm_service = make_alarm_service(repo=make_repo(get_return=None))

        with pytest.raises(AlarmNotFoundError):
            await alarm_service.snooze(uuid.uuid4())

    async def test_raises_when_alarm_not_running(self) -> None:
        alarm = make_alarm(status=AlarmStatus.SCHEDULED)
        alarm_service = make_alarm_service(repo=make_repo(get_return=alarm))

        with pytest.raises(AlarmNotRunningError):
            await alarm_service.snooze(alarm.id)

    async def test_snoozes_with_custom_minutes(self) -> None:
        alarm = make_alarm(status=AlarmStatus.INTRO)
        alarm_service = make_alarm_service(repo=make_repo(get_return=alarm))

        await alarm_service.snooze(alarm.id, minutes=5)

        assert alarm.status == AlarmStatus.SCHEDULED


class TestAlarmServiceListAlarms:
    async def test_returns_all_alarms_from_repository(self) -> None:
        alarm_a = make_alarm(status=AlarmStatus.SCHEDULED)
        alarm_b = make_alarm(status=AlarmStatus.INACTIVE)
        repo = make_repo(get_all_return=[alarm_a, alarm_b])
        alarm_service = make_alarm_service(repo=repo)

        result = await alarm_service.list_alarms()

        assert list(result) == [alarm_a, alarm_b]

    async def test_returns_empty_sequence_when_no_alarms(self) -> None:
        repo = make_repo(get_all_return=[])
        alarm_service = make_alarm_service(repo=repo)

        result = await alarm_service.list_alarms()

        assert len(result) == 0

    async def test_delegates_to_repository_get_all(self) -> None:
        repo = make_repo()
        alarm_service = make_alarm_service(repo=repo)

        await alarm_service.list_alarms()

        repo.get_all.assert_awaited_once()
