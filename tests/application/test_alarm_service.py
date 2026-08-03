import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from huerise.application.alarm_service import (
    AlarmRunner,
    AlarmScheduler,
    AlarmService,
    AudioPlayer,
    Lights,
)
from huerise.domain import (
    AlarmNotFoundError,
    AlarmNotRunningError,
    AlarmStatus,
    AlarmType,
    Weekday,
)
from huerise.domain.views import Schedule
from tests.application.conftest import make_alarm, make_repo


def make_audio() -> AudioPlayer:
    audio = MagicMock(spec=AudioPlayer)
    audio.play = AsyncMock()
    audio.stop = AsyncMock()
    audio.set_volume = AsyncMock()
    return audio


def make_lights() -> Lights:
    lights = MagicMock(spec=Lights)
    lights.activate_scene = AsyncMock()
    lights.set_brightness = AsyncMock()
    return lights


def make_service(
    repo=None,
    audio=None,
):
    return AlarmService(
        alarm_repository=repo if repo is not None else make_repo(),
        audio=audio if audio is not None else make_audio(),
    )


class TestAlarmServiceActivate:
    async def test_returns_the_alarm(self) -> None:
        alarm = make_alarm(status=AlarmStatus.INACTIVE)
        service = make_service(repo=make_repo(get_return=alarm))

        result = await service.activate(alarm.id)

        assert result is alarm

    async def test_sets_status_to_scheduled(self) -> None:
        alarm = make_alarm(status=AlarmStatus.INACTIVE)
        service = make_service(repo=make_repo(get_return=alarm))

        await service.activate(alarm.id)

        assert alarm.status == AlarmStatus.SCHEDULED

    async def test_saves_alarm_after_activation(self) -> None:
        alarm = make_alarm(status=AlarmStatus.INACTIVE)
        repo = make_repo(get_return=alarm)
        service = make_service(repo=repo)

        await service.activate(alarm.id)

        repo.save.assert_awaited_once_with(alarm)

    async def test_raises_when_alarm_not_found(self) -> None:
        service = make_service(repo=make_repo(get_return=None))

        with pytest.raises(AlarmNotFoundError):
            await service.activate(uuid.uuid4())


class TestAlarmServiceCancel:
    async def test_returns_the_alarm(self) -> None:
        alarm = make_alarm(status=AlarmStatus.SCHEDULED)
        service = make_service(repo=make_repo(get_return=alarm))

        result = await service.cancel(alarm.id)

        assert result is alarm

    async def test_sets_status_to_cancelled(self) -> None:
        alarm = make_alarm(status=AlarmStatus.SCHEDULED)
        service = make_service(repo=make_repo(get_return=alarm))

        await service.cancel(alarm.id)

        assert alarm.status == AlarmStatus.CANCELLED

    async def test_saves_alarm_after_cancellation(self) -> None:
        alarm = make_alarm(status=AlarmStatus.SCHEDULED)
        repo = make_repo(get_return=alarm)
        service = make_service(repo=repo)

        await service.cancel(alarm.id)

        repo.save.assert_awaited_once_with(alarm)

    async def test_raises_when_alarm_not_found(self) -> None:
        service = make_service(repo=make_repo(get_return=None))

        with pytest.raises(AlarmNotFoundError):
            await service.cancel(uuid.uuid4())


class TestAlarmServiceCreateOneTime:
    async def test_returns_created_alarm(self) -> None:
        service = make_service()

        result = await service.create_one_time(
            label="Sun", hour=7, minute=30, room_name="Bedroom"
        )

        assert result is not None
        assert result.label == "Sun"

    async def test_alarm_has_correct_schedule(self) -> None:
        service = make_service()

        result = await service.create_one_time(
            label="Sun", hour=6, minute=45, room_name="Bedroom"
        )

        assert result.schedule.hour == 6
        assert result.schedule.minute == 45

    async def test_alarm_type_is_one_time(self) -> None:
        service = make_service()

        result = await service.create_one_time(
            label="Sun", hour=7, minute=0, room_name="Bedroom"
        )

        assert result.alarm_type == AlarmType.ONE_TIME

    async def test_alarm_is_scheduled_on_creation(self) -> None:
        service = make_service()

        result = await service.create_one_time(
            label="Sun", hour=7, minute=0, room_name="Bedroom"
        )

        assert result.status == AlarmStatus.SCHEDULED

    async def test_saves_alarm_to_repository(self) -> None:
        repo = make_repo()
        service = make_service(repo=repo)

        result = await service.create_one_time(
            label="Sun", hour=7, minute=0, room_name="Bedroom"
        )

        repo.save.assert_awaited_once_with(result)

    async def test_uses_default_audio_files(self) -> None:
        service = make_service()

        result = await service.create_one_time(
            label="Sun", hour=7, minute=0, room_name="Bedroom"
        )

        assert result.intro_config.audio_file == "wake-up-bowls.mp3"
        assert result.ringtone_config.audio_file == "get-up-aurora.mp3"

    async def test_uses_custom_audio_files_when_provided(self) -> None:
        service = make_service()

        result = await service.create_one_time(
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
        service = make_service()

        result = await service.create_recurring(
            label="Weekday",
            hour=7,
            minute=0,
            days=frozenset({Weekday.MON, Weekday.FRI}),
            room_name="Bedroom",
        )

        assert result is not None
        assert result.label == "Weekday"

    async def test_alarm_type_is_recurring(self) -> None:
        service = make_service()

        result = await service.create_recurring(
            label="Weekday",
            hour=7,
            minute=0,
            days=frozenset({Weekday.MON}),
            room_name="Bedroom",
        )

        assert result.alarm_type == AlarmType.RECURRING

    async def test_alarm_has_correct_days(self) -> None:
        service = make_service()

        result = await service.create_recurring(
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
        service = make_service()

        result = await service.create_recurring(
            label="Weekday",
            hour=7,
            minute=0,
            days=frozenset({Weekday.MON}),
            room_name="Bedroom",
        )

        assert result.series_id is not None

    async def test_alarm_is_scheduled_on_creation(self) -> None:
        service = make_service()

        result = await service.create_recurring(
            label="Weekday",
            hour=7,
            minute=0,
            days=frozenset({Weekday.MON}),
            room_name="Bedroom",
        )

        assert result.status == AlarmStatus.SCHEDULED

    async def test_saves_alarm_to_repository(self) -> None:
        repo = make_repo()
        service = make_service(repo=repo)

        result = await service.create_recurring(
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
        service = make_service(repo=make_repo(get_return=alarm))

        result = await service.deactivate(alarm.id)

        assert result is alarm

    async def test_sets_status_to_inactive(self) -> None:
        alarm = make_alarm(status=AlarmStatus.SCHEDULED)
        service = make_service(repo=make_repo(get_return=alarm))

        await service.deactivate(alarm.id)

        assert alarm.status == AlarmStatus.INACTIVE

    async def test_saves_alarm_after_deactivation(self) -> None:
        alarm = make_alarm(status=AlarmStatus.SCHEDULED)
        repo = make_repo(get_return=alarm)
        service = make_service(repo=repo)

        await service.deactivate(alarm.id)

        repo.save.assert_awaited_once_with(alarm)

    async def test_raises_when_alarm_not_found(self) -> None:
        service = make_service(repo=make_repo(get_return=None))

        with pytest.raises(AlarmNotFoundError):
            await service.deactivate(uuid.uuid4())


class TestAlarmServiceDelete:
    async def test_deletes_existing_alarm(self) -> None:
        alarm = make_alarm(status=AlarmStatus.SCHEDULED)
        repo = make_repo(get_return=alarm)
        service = make_service(repo=repo)

        await service.delete(alarm.id)

        repo.delete.assert_awaited_once_with(alarm.id)

    async def test_returns_none(self) -> None:
        alarm = make_alarm(status=AlarmStatus.SCHEDULED)
        repo = make_repo(get_return=alarm)
        service = make_service(repo=repo)

        result = await service.delete(alarm.id)

        assert result is None

    async def test_raises_when_alarm_not_found(self) -> None:
        service = make_service(repo=make_repo(get_return=None))

        with pytest.raises(AlarmNotFoundError):
            await service.delete(uuid.uuid4())

    async def test_does_not_delete_when_not_found(self) -> None:
        repo = make_repo(get_return=None)
        service = make_service(repo=repo)

        with pytest.raises(AlarmNotFoundError):
            await service.delete(uuid.uuid4())

        repo.delete.assert_not_awaited()


class TestAlarmServiceDeleteSeries:
    async def test_deletes_all_alarms_in_series(self) -> None:
        series_id = uuid.uuid4()
        alarm_a = make_alarm(status=AlarmStatus.SCHEDULED, series_id=series_id)
        alarm_b = make_alarm(status=AlarmStatus.SCHEDULED, series_id=series_id)
        repo = make_repo(get_all_return=[alarm_a, alarm_b])
        service = make_service(repo=repo)

        await service.delete_series(series_id)

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
        service = make_service(repo=repo)

        await service.delete_series(series_id)

        repo.delete.assert_awaited_once_with(alarm_in_series.id)

    async def test_does_nothing_when_series_has_no_alarms(self) -> None:
        series_id = uuid.uuid4()
        repo = make_repo(get_all_return=[])
        service = make_service(repo=repo)

        await service.delete_series(series_id)

        repo.delete.assert_not_awaited()


class TestAlarmServiceSetVolume:
    async def test_calls_set_volume_with_given_volume(self) -> None:
        audio = make_audio()
        service = make_service(audio=audio)

        await service.set_volume(75)

        audio.set_volume.assert_awaited_once_with(75)

    async def test_calls_set_volume_with_zero(self) -> None:
        audio = make_audio()
        service = make_service(audio=audio)

        await service.set_volume(0)

        audio.set_volume.assert_awaited_once_with(0)

    async def test_calls_set_volume_with_max(self) -> None:
        audio = make_audio()
        service = make_service(audio=audio)

        await service.set_volume(100)

        audio.set_volume.assert_awaited_once_with(100)


class TestAlarmServiceSnooze:
    async def test_returns_the_alarm(self) -> None:
        alarm = make_alarm(status=AlarmStatus.RINGING)
        service = make_service(repo=make_repo(get_return=alarm))

        result = await service.snooze(alarm.id)

        assert result is alarm

    async def test_sets_status_to_scheduled(self) -> None:
        alarm = make_alarm(status=AlarmStatus.RINGING)
        service = make_service(repo=make_repo(get_return=alarm))

        await service.snooze(alarm.id)

        assert alarm.status == AlarmStatus.SCHEDULED

    async def test_stops_audio(self) -> None:
        alarm = make_alarm(status=AlarmStatus.RINGING)
        audio = make_audio()
        service = make_service(repo=make_repo(get_return=alarm), audio=audio)

        await service.snooze(alarm.id)

        audio.stop.assert_awaited_once()

    async def test_saves_alarm_after_snooze(self) -> None:
        alarm = make_alarm(status=AlarmStatus.RINGING)
        repo = make_repo(get_return=alarm)
        service = make_service(repo=repo)

        await service.snooze(alarm.id)

        repo.save.assert_awaited_once_with(alarm)

    async def test_raises_when_alarm_not_found(self) -> None:
        service = make_service(repo=make_repo(get_return=None))

        with pytest.raises(AlarmNotFoundError):
            await service.snooze(uuid.uuid4())

    async def test_raises_when_alarm_not_running(self) -> None:
        alarm = make_alarm(status=AlarmStatus.SCHEDULED)
        service = make_service(repo=make_repo(get_return=alarm))

        with pytest.raises(AlarmNotRunningError):
            await service.snooze(alarm.id)

    async def test_snoozes_with_custom_minutes(self) -> None:
        alarm = make_alarm(status=AlarmStatus.INTRO)
        service = make_service(repo=make_repo(get_return=alarm))

        await service.snooze(alarm.id, minutes=5)

        assert alarm.status == AlarmStatus.SCHEDULED


class TestAlarmServiceListAlarms:
    async def test_returns_all_alarms_from_repository(self) -> None:
        alarm_a = make_alarm(status=AlarmStatus.SCHEDULED)
        alarm_b = make_alarm(status=AlarmStatus.INACTIVE)
        repo = make_repo(get_all_return=[alarm_a, alarm_b])
        service = make_service(repo=repo)

        result = await service.list_alarms()

        assert list(result) == [alarm_a, alarm_b]

    async def test_returns_empty_sequence_when_no_alarms(self) -> None:
        repo = make_repo(get_all_return=[])
        service = make_service(repo=repo)

        result = await service.list_alarms()

        assert len(result) == 0

    async def test_delegates_to_repository_get_all(self) -> None:
        repo = make_repo()
        service = make_service(repo=repo)

        await service.list_alarms()

        repo.get_all.assert_awaited_once()


class TestAlarmRunnerStateTransitions:
    async def test_alarm_reaches_completed_status(self) -> None:
        alarm = make_alarm(status=AlarmStatus.SCHEDULED)
        repo = make_repo()
        runner = AlarmRunner(lights=make_lights(), audio=make_audio(), repo=repo)
        runner._run_sunrise = AsyncMock()  # type: ignore[method-assign]
        runner._run_ringtone = AsyncMock()  # type: ignore[method-assign]

        await runner.run(alarm)

        assert alarm.status == AlarmStatus.COMPLETED

    async def test_repo_save_called_after_each_transition(self) -> None:
        alarm = make_alarm(status=AlarmStatus.SCHEDULED)
        repo = make_repo()
        runner = AlarmRunner(lights=make_lights(), audio=make_audio(), repo=repo)
        runner._run_sunrise = AsyncMock()  # type: ignore[method-assign]
        runner._run_ringtone = AsyncMock()  # type: ignore[method-assign]

        await runner.run(alarm)

        assert repo.save.await_count == 3

    async def test_run_sunrise_is_called(self) -> None:
        alarm = make_alarm(status=AlarmStatus.SCHEDULED)
        repo = make_repo()
        runner = AlarmRunner(lights=make_lights(), audio=make_audio(), repo=repo)
        runner._run_sunrise = AsyncMock()  # type: ignore[method-assign]
        runner._run_ringtone = AsyncMock()  # type: ignore[method-assign]

        await runner.run(alarm)

        runner._run_sunrise.assert_awaited_once_with(alarm)

    async def test_run_ringtone_is_called(self) -> None:
        alarm = make_alarm(status=AlarmStatus.SCHEDULED)
        repo = make_repo()
        runner = AlarmRunner(lights=make_lights(), audio=make_audio(), repo=repo)
        runner._run_sunrise = AsyncMock()  # type: ignore[method-assign]
        runner._run_ringtone = AsyncMock()  # type: ignore[method-assign]

        await runner.run(alarm)

        runner._run_ringtone.assert_awaited_once_with(alarm)


class TestAlarmRunnerRunSunrise:
    async def test_activates_light_scene(self) -> None:
        alarm = make_alarm(status=AlarmStatus.SCHEDULED)
        lights = make_lights()
        runner = AlarmRunner(lights=lights, audio=make_audio(), repo=make_repo())

        with patch("huerise.application.alarm_service.asyncio.create_task"):
            await runner._run_sunrise(alarm)

        lights.activate_scene.assert_awaited_once_with(
            alarm.sunrise_config.room_name,
            alarm.sunrise_config.scene_name,
        )

    async def test_sets_brightness_for_each_step(self) -> None:
        alarm = make_alarm(status=AlarmStatus.SCHEDULED)
        lights = make_lights()
        runner = AlarmRunner(lights=lights, audio=make_audio(), repo=make_repo())

        with patch("huerise.application.alarm_service.asyncio.create_task"):
            await runner._run_sunrise(alarm)

        # make_alarm uses steps=1
        assert lights.set_brightness.await_count == alarm.sunrise_config.steps


class TestAlarmRunnerRunRingtone:
    async def test_stops_audio_before_playing(self) -> None:
        alarm = make_alarm(status=AlarmStatus.SCHEDULED)
        audio = make_audio()
        runner = AlarmRunner(lights=make_lights(), audio=audio, repo=make_repo())

        await runner._run_ringtone(alarm)

        audio.stop.assert_awaited_once()

    async def test_plays_ringtone_with_correct_file_and_volume(self) -> None:
        alarm = make_alarm(status=AlarmStatus.SCHEDULED)
        audio = make_audio()
        runner = AlarmRunner(lights=make_lights(), audio=audio, repo=make_repo())

        await runner._run_ringtone(alarm)

        audio.play.assert_awaited_once_with(
            alarm.ringtone_config.audio_file,
            alarm.ringtone_config.volume,
        )


# April 6, 2026 is a Monday (weekday() == 0)
_MONDAY_7_00 = datetime(2026, 4, 6, 7, 0, tzinfo=timezone.utc)
_MONDAY_8_30 = datetime(2026, 4, 6, 8, 30, tzinfo=timezone.utc)


def make_runner() -> AlarmRunner:
    return MagicMock(spec=AlarmRunner)


class TestAlarmSchedulerShouldTrigger:
    def test_returns_true_when_hour_and_minute_match_no_recurrence(self) -> None:
        schedule = Schedule(hour=7, minute=0)
        assert AlarmScheduler._should_trigger(schedule, _MONDAY_7_00) is True

    def test_returns_false_when_hour_does_not_match(self) -> None:
        schedule = Schedule(hour=8, minute=0)
        assert AlarmScheduler._should_trigger(schedule, _MONDAY_7_00) is False

    def test_returns_false_when_minute_does_not_match(self) -> None:
        schedule = Schedule(hour=7, minute=15)
        assert AlarmScheduler._should_trigger(schedule, _MONDAY_7_00) is False

    def test_returns_true_when_weekday_in_recurrence(self) -> None:
        schedule = Schedule(hour=7, minute=0, recurrence=frozenset({Weekday.MON}))
        assert AlarmScheduler._should_trigger(schedule, _MONDAY_7_00) is True

    def test_returns_false_when_weekday_not_in_recurrence(self) -> None:
        schedule = Schedule(hour=7, minute=0, recurrence=frozenset({Weekday.TUE}))
        assert AlarmScheduler._should_trigger(schedule, _MONDAY_7_00) is False

    def test_returns_true_when_one_of_multiple_days_matches(self) -> None:
        schedule = Schedule(
            hour=7,
            minute=0,
            recurrence=frozenset({Weekday.MON, Weekday.WED, Weekday.FRI}),
        )
        assert AlarmScheduler._should_trigger(schedule, _MONDAY_7_00) is True


class TestAlarmSchedulerTick:
    async def test_triggers_alarm_due_at_current_time(self) -> None:
        alarm = make_alarm(status=AlarmStatus.SCHEDULED, hour=7, minute=0)
        repo = make_repo(get_scheduled_return=[alarm])
        runner = make_runner()
        runner.run = AsyncMock()
        scheduler = AlarmScheduler(repo=repo, runner=runner)

        with patch("huerise.application.alarm_service.datetime") as mock_dt:
            mock_dt.now.return_value = _MONDAY_7_00
            with patch(
                "huerise.application.alarm_service.asyncio.create_task"
            ) as mock_task:
                await scheduler._tick()

        mock_task.assert_called_once()

    async def test_does_not_trigger_alarm_at_wrong_time(self) -> None:
        alarm = make_alarm(status=AlarmStatus.SCHEDULED, hour=8, minute=30)
        repo = make_repo(get_scheduled_return=[alarm])
        runner = make_runner()
        scheduler = AlarmScheduler(repo=repo, runner=runner)

        with patch("huerise.application.alarm_service.datetime") as mock_dt:
            mock_dt.now.return_value = _MONDAY_7_00
            with patch(
                "huerise.application.alarm_service.asyncio.create_task"
            ) as mock_task:
                await scheduler._tick()

        mock_task.assert_not_called()

    async def test_skips_tick_when_repository_raises(self) -> None:
        repo = make_repo()
        repo.get_scheduled = AsyncMock(side_effect=RuntimeError("db error"))
        runner = make_runner()
        scheduler = AlarmScheduler(repo=repo, runner=runner)

        with patch("huerise.application.alarm_service.datetime") as mock_dt:
            mock_dt.now.return_value = _MONDAY_7_00
            with patch(
                "huerise.application.alarm_service.asyncio.create_task"
            ) as mock_task:
                await scheduler._tick()

        mock_task.assert_not_called()

    async def test_triggers_only_alarms_matching_current_time(self) -> None:
        alarm_due = make_alarm(status=AlarmStatus.SCHEDULED, hour=7, minute=0)
        alarm_not_due = make_alarm(status=AlarmStatus.SCHEDULED, hour=8, minute=30)
        repo = make_repo(get_scheduled_return=[alarm_due, alarm_not_due])
        runner = make_runner()
        runner.run = AsyncMock()
        scheduler = AlarmScheduler(repo=repo, runner=runner)

        with patch("huerise.application.alarm_service.datetime") as mock_dt:
            mock_dt.now.return_value = _MONDAY_7_00
            with patch(
                "huerise.application.alarm_service.asyncio.create_task"
            ) as mock_task:
                await scheduler._tick()

        assert mock_task.call_count == 1
