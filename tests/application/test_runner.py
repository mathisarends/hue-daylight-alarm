from datetime import UTC, datetime, timedelta
from unittest.mock import patch

from huerise.features.alarm.domain import OccurrenceState
from huerise.features.devices.domain import SunriseRamp, sunrise_steps
from huerise.features.events.domain import (
    OccurrenceDismissed,
    OccurrenceFailed,
    OccurrenceProgress,
    OccurrenceRinging,
    OccurrenceStarted,
)
from huerise.features.runner.application import AlarmRunner
from tests.application.conftest import (
    FakeUnitOfWork,
    FakeUnitOfWorkFactory,
    InMemoryAlarmRepository,
    InMemoryOccurrenceRepository,
    InMemoryProfileRepository,
    RecordingPublisher,
    make_alarm,
    make_audio,
    make_lights,
    make_occurrence,
    make_profile,
)

NOW = datetime(2026, 8, 3, 5, 0, tzinfo=UTC)
STEP = timedelta(seconds=6)


def ramp_of(profile) -> SunriseRamp:
    sunrise = profile.sunrise_config
    return SunriseRamp(
        duration=sunrise.duration,
        brightness_start=sunrise.brightness_start,
        brightness_end=sunrise.brightness_end,
    )


def make_runner(
    sunrise_duration: timedelta = timedelta(minutes=1),
    events: RecordingPublisher | None = None,
):
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
        events=events if events is not None else RecordingPublisher(),
        step_interval=STEP,
    )
    return runner, occurrence, occurrences, lights, audio, alarm, profile


class TestRun:
    async def test_runs_the_full_sequence(self) -> None:
        runner, occurrence, occurrences, lights, audio, _, profile = make_runner()

        with patch("asyncio.sleep"):
            await runner.run(occurrence)

        lights.activate_scene.assert_awaited_once_with(
            profile.sunrise_config.scene_id,
            brightness=profile.sunrise_config.brightness_start,
        )
        audio.play.assert_any_await(
            profile.ringtone_config.sound_id, profile.ringtone_config.volume
        )
        assert occurrences.items[occurrence.id].state is OccurrenceState.DISMISSED

    async def test_dimming_follows_the_derived_steps(self) -> None:
        runner, occurrence, _, lights, _, _, profile = make_runner()

        with patch("asyncio.sleep"):
            await runner.run(occurrence)

        expected = len(list(sunrise_steps(ramp_of(profile), STEP)))
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


class TestPublishedEvents:
    async def test_announces_the_sunrise_before_it_starts(self) -> None:
        events = RecordingPublisher()
        runner, occurrence, _, _, _, alarm, profile = make_runner(events=events)

        with patch("asyncio.sleep"):
            await runner.run(occurrence)

        started = events.only(OccurrenceStarted)
        assert started.label == alarm.label
        assert started.room_name == alarm.room_name
        assert started.sunrise_seconds == profile.sunrise_config.duration.seconds

    async def test_reports_progress_once_per_brightness_step(self) -> None:
        events = RecordingPublisher()
        runner, occurrence, _, _, _, _, profile = make_runner(events=events)

        with patch("asyncio.sleep"):
            await runner.run(occurrence)

        progress = events.of_type(OccurrenceProgress)
        assert [event.brightness for event in progress] == [
            step.brightness for step in sunrise_steps(ramp_of(profile), STEP)
        ]
        assert progress[-1].percent == 100.0

    async def test_progress_stops_when_the_sunrise_is_interrupted(self) -> None:
        events = RecordingPublisher()
        runner, occurrence, occurrences, lights, _, _, _ = make_runner(events=events)

        async def dismiss_after_first_step(*args, **kwargs) -> None:
            stored = occurrences.items[occurrence.id]
            if stored.state is OccurrenceState.SUNRISE:
                stored.dismiss(NOW)

        lights.set_brightness.side_effect = dismiss_after_first_step

        with patch("asyncio.sleep"):
            await runner.run(occurrence)

        assert len(events.of_type(OccurrenceProgress)) == 1
        assert events.of_type(OccurrenceRinging) == []

    async def test_announces_the_ringtone_it_is_about_to_play(self) -> None:
        events = RecordingPublisher()
        runner, occurrence, _, _, _, _, profile = make_runner(events=events)

        with patch("asyncio.sleep"):
            await runner.run(occurrence)

        ringing = events.only(OccurrenceRinging)
        assert ringing.sound_id == profile.ringtone_config.sound_id
        assert ringing.volume == profile.ringtone_config.volume

    async def test_announces_the_finished_run(self) -> None:
        events = RecordingPublisher()
        runner, occurrence, _, _, _, _, _ = make_runner(events=events)

        with patch("asyncio.sleep"):
            await runner.run(occurrence)

        assert events.only(OccurrenceDismissed).occurrence.id == occurrence.id

    async def test_announces_a_failure_with_its_reason(self) -> None:
        events = RecordingPublisher()
        runner, occurrence, _, lights, _, _, _ = make_runner(events=events)
        lights.activate_scene.side_effect = RuntimeError("bridge unreachable")

        with patch("asyncio.sleep"):
            await runner.run(occurrence)

        failed = events.only(OccurrenceFailed).occurrence
        assert "bridge unreachable" in (failed.failure_reason or "")
