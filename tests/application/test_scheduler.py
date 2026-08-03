from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from huerise.application import AlarmRunner, AlarmScheduler, AudioPlayer, Lights
from huerise.domain import AlarmStatus, Weekday
from huerise.domain.views import Schedule
from tests.application.conftest import make_alarm, make_repo


def make_lights() -> Lights:
    lights = MagicMock(spec=Lights)
    lights.activate_scene = AsyncMock()
    lights.set_brightness = AsyncMock()
    return lights


def make_audio() -> AudioPlayer:
    audio = MagicMock(spec=AudioPlayer)
    audio.play = AsyncMock()
    audio.stop = AsyncMock()
    audio.set_volume = AsyncMock()
    return audio


def make_runner() -> AlarmRunner:
    return MagicMock(spec=AlarmRunner)


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

        with patch("huerise.application.scheduler.asyncio.create_task"):
            await runner._run_sunrise(alarm)

        lights.activate_scene.assert_awaited_once_with(
            alarm.sunrise_config.room_name,
            alarm.sunrise_config.scene_name,
        )

    async def test_sets_brightness_for_each_step(self) -> None:
        alarm = make_alarm(status=AlarmStatus.SCHEDULED)
        lights = make_lights()
        runner = AlarmRunner(lights=lights, audio=make_audio(), repo=make_repo())

        with patch("huerise.application.scheduler.asyncio.create_task"):
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

        with patch("huerise.application.scheduler.datetime") as mock_dt:
            mock_dt.now.return_value = _MONDAY_7_00
            with patch(
                "huerise.application.scheduler.asyncio.create_task"
            ) as mock_task:
                await scheduler._tick()

        mock_task.assert_called_once()

    async def test_does_not_trigger_alarm_at_wrong_time(self) -> None:
        alarm = make_alarm(status=AlarmStatus.SCHEDULED, hour=8, minute=30)
        repo = make_repo(get_scheduled_return=[alarm])
        runner = make_runner()
        scheduler = AlarmScheduler(repo=repo, runner=runner)

        with patch("huerise.application.scheduler.datetime") as mock_dt:
            mock_dt.now.return_value = _MONDAY_7_00
            with patch(
                "huerise.application.scheduler.asyncio.create_task"
            ) as mock_task:
                await scheduler._tick()

        mock_task.assert_not_called()

    async def test_skips_tick_when_repository_raises(self) -> None:
        repo = make_repo()
        repo.get_scheduled = AsyncMock(side_effect=RuntimeError("db error"))
        runner = make_runner()
        scheduler = AlarmScheduler(repo=repo, runner=runner)

        with patch("huerise.application.scheduler.datetime") as mock_dt:
            mock_dt.now.return_value = _MONDAY_7_00
            with patch(
                "huerise.application.scheduler.asyncio.create_task"
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

        with patch("huerise.application.scheduler.datetime") as mock_dt:
            mock_dt.now.return_value = _MONDAY_7_00
            with patch(
                "huerise.application.scheduler.asyncio.create_task"
            ) as mock_task:
                await scheduler._tick()

        assert mock_task.call_count == 1
