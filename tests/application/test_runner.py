from datetime import UTC, datetime, timedelta
from unittest.mock import patch

from huerise.features.alarm.domain import OccurrenceState, SunriseConfig
from huerise.features.runner.application import AlarmRunner
from huerise.features.runner.application.sunrise import sunrise_steps
from tests.application.conftest import (
    FakeUnitOfWork,
    FakeUnitOfWorkFactory,
    InMemoryAlarmRepository,
    InMemoryOccurrenceRepository,
    InMemoryProfileRepository,
    make_alarm,
    make_audio,
    make_lights,
    make_occurrence,
    make_profile,
)

NOW = datetime(2026, 8, 3, 5, 0, tzinfo=UTC)
STEP = timedelta(seconds=6)


def make_runner(sunrise_duration: timedelta = timedelta(minutes=1)):
    profile = make_profile(sunrise_duration=sunrise_duration)
    alarm = make_alarm(profile_id=profile.id)
    occurrence = make_occurrence(alarm.id, NOW, OccurrenceState.SUNRISE)
    occurrences = InMemoryOccurrenceRepository([occurrence])

    unit_of_work = FakeUnitOfWork(
        alarms=InMemoryAlarmRepository([alarm]),
        profiles=InMemoryProfileRepository([profile]),
        occurrences=occurrences,
    )
    lights, audio = make_lights(), make_audio()
    runner = AlarmRunner(
        lights=lights,
        audio=audio,
        unit_of_work_factory=FakeUnitOfWorkFactory(unit_of_work),
        step_interval=STEP,
    )
    return runner, occurrence, occurrences, lights, audio, alarm, profile


class TestSunriseSteps:
    def test_derives_step_count_from_duration(self) -> None:
        config = SunriseConfig(duration=timedelta(minutes=1))

        assert len(list(sunrise_steps(config, STEP))) == 10

    def test_walks_from_start_to_end_brightness(self) -> None:
        config = SunriseConfig(
            duration=timedelta(minutes=1), brightness_start=10, brightness_end=100
        )

        steps = list(sunrise_steps(config, STEP))

        assert steps[0] == 10
        assert steps[-1] == 100
        assert steps == sorted(steps)

    def test_always_yields_at_least_one_step(self) -> None:
        config = SunriseConfig(duration=timedelta(0))

        assert list(sunrise_steps(config, STEP)) == [1]


class TestRun:
    async def test_runs_the_full_sequence(self) -> None:
        runner, occurrence, occurrences, lights, audio, alarm, profile = make_runner()

        with patch("asyncio.sleep"):
            await runner.run(occurrence)

        lights.activate_scene.assert_awaited_once_with(
            alarm.room_name, profile.sunrise_config.scene_name
        )
        audio.play.assert_any_await(
            profile.ringtone_config.sound_id, profile.ringtone_config.volume
        )
        assert occurrences.items[occurrence.id].state is OccurrenceState.DISMISSED

    async def test_dimming_follows_the_derived_steps(self) -> None:
        runner, occurrence, _, lights, _, _, profile = make_runner()

        with patch("asyncio.sleep"):
            await runner.run(occurrence)

        expected = len(list(sunrise_steps(profile.sunrise_config, STEP)))
        assert lights.set_brightness.await_count == expected

    async def test_stops_when_the_occurrence_is_dismissed_mid_sunrise(self) -> None:
        runner, occurrence, occurrences, lights, _, _, _ = make_runner()

        async def dismiss_after_first_step(*args, **kwargs) -> None:
            stored = occurrences.items[occurrence.id]
            if stored.state is OccurrenceState.SUNRISE:
                stored.dismiss(NOW)

        lights.set_brightness.side_effect = dismiss_after_first_step

        with patch("asyncio.sleep"):
            await runner.run(occurrence)

        assert lights.set_brightness.await_count == 1
        assert occurrences.items[occurrence.id].state is OccurrenceState.DISMISSED

    async def test_marks_the_occurrence_failed_on_error(self) -> None:
        runner, occurrence, occurrences, lights, _, _, _ = make_runner()
        lights.activate_scene.side_effect = RuntimeError("bridge unreachable")

        with patch("asyncio.sleep"):
            await runner.run(occurrence)

        stored = occurrences.items[occurrence.id]
        assert stored.state is OccurrenceState.FAILED
        assert "bridge unreachable" in (stored.failure_reason or "")
