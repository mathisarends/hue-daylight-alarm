from datetime import UTC, datetime, timedelta
from unittest.mock import call, patch

from huerise.features.alarm.domain import AlarmDefect, AlarmField, OccurrenceState
from huerise.features.events.domain import (
    AlarmUpdated,
    OccurrenceDismissed,
    OccurrenceFailed,
    OccurrenceProgress,
    OccurrenceStarted,
)
from huerise.features.lighting.domain import Room, Scene, SunriseRamp, sunrise_steps
from huerise.features.runner.application import AlarmRunner
from tests.application.conftest import (
    ROOM_ID,
    SCENE_ID,
    FakeUnitOfWork,
    FakeUnitOfWorkFactory,
    InMemoryAlarmRepository,
    InMemoryOccurrenceRepository,
    InMemoryProfileRepository,
    RecordingPublisher,
    make_alarm,
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
    lights = make_lights()
    runner = AlarmRunner(
        lights=lights,
        unit_of_work_factory=FakeUnitOfWorkFactory(unit_of_work),
        events=events if events is not None else RecordingPublisher(),
        step_interval=STEP,
    )
    return runner, occurrence, occurrences, lights, alarm, profile


class TestRun:
    async def test_runs_the_full_sequence(self) -> None:
        runner, occurrence, occurrences, lights, _, profile = make_runner()

        with patch("asyncio.sleep"):
            await runner.run(occurrence)

        assert lights.activate_scene.await_args_list == [
            call(
                profile.sunrise_config.scene_id,
                brightness=profile.sunrise_config.brightness_start,
            ),
            call(profile.sunrise_config.scene_id),
        ]
        assert occurrences.items[occurrence.id].state is OccurrenceState.DISMISSED

    async def test_dimming_follows_the_derived_steps(self) -> None:
        runner, occurrence, _, lights, _, profile = make_runner()

        with patch("asyncio.sleep"):
            await runner.run(occurrence)

        expected = len(list(sunrise_steps(ramp_of(profile), STEP)))
        assert lights.set_brightness.await_count == expected

    async def test_stops_when_the_occurrence_is_dismissed_mid_sunrise(self) -> None:
        runner, occurrence, occurrences, lights, _, _ = make_runner()

        async def dismiss_after_first_step(*args, **kwargs) -> None:
            stored = occurrences.items[occurrence.id]
            if stored.state is OccurrenceState.SUNRISE:
                stored.dismiss(NOW)

        lights.set_brightness.side_effect = dismiss_after_first_step

        with patch("asyncio.sleep"):
            await runner.run(occurrence)

        assert lights.set_brightness.await_count == 1
        assert occurrences.items[occurrence.id].state is OccurrenceState.DISMISSED


class TestFinishingWithoutLight:
    """A bridge or room problem must not cost the occurrence its finish."""

    async def test_finishes_when_the_bridge_cannot_be_reached(self) -> None:
        runner, occurrence, occurrences, lights, _, _ = make_runner()
        lights.activate_scene.side_effect = RuntimeError("bridge unreachable")

        with patch("asyncio.sleep"):
            await runner.run(occurrence)

        assert occurrences.items[occurrence.id].state is OccurrenceState.DISMISSED

    async def test_finishes_when_the_room_is_gone(self) -> None:
        runner, occurrence, occurrences, lights, _, _ = make_runner()
        lights.list_rooms.return_value = []

        with patch("asyncio.sleep"):
            await runner.run(occurrence)

        assert occurrences.items[occurrence.id].state is OccurrenceState.DISMISSED

    async def test_a_missing_room_is_recorded_on_the_alarm(self) -> None:
        events = RecordingPublisher()
        runner, occurrence, _, lights, alarm, _ = make_runner(events=events)
        lights.list_rooms.return_value = []

        with patch("asyncio.sleep"):
            await runner.run(occurrence)

        assert alarm.defect is AlarmDefect.ROOM_MISSING
        published = events.only(AlarmUpdated)
        assert published.changed == [AlarmField.DEFECT]
        assert published.alarm.defect is AlarmDefect.ROOM_MISSING

    async def test_a_missing_scene_is_recorded_on_the_alarm(self) -> None:
        runner, occurrence, _, lights, alarm, _ = make_runner()
        lights.list_rooms.return_value = [Room(id=ROOM_ID, name="Bedroom", scenes=())]

        with patch("asyncio.sleep"):
            await runner.run(occurrence)

        assert alarm.defect is AlarmDefect.SCENE_MISSING

    async def test_a_defect_already_known_is_not_reported_again(self) -> None:
        events = RecordingPublisher()
        runner, occurrence, occurrences, lights, alarm, _ = make_runner(events=events)
        alarm.set_defect(AlarmDefect.ROOM_MISSING)
        lights.list_rooms.return_value = []

        with patch("asyncio.sleep"):
            await runner.run(occurrence)

        assert events.of_type(AlarmUpdated) == []
        assert occurrences.items[occurrence.id].state is OccurrenceState.DISMISSED

    async def test_a_scene_too_dim_to_ramp_still_finishes(self) -> None:
        """A curve that cannot be walked is a setting, not a broken alarm."""
        events = RecordingPublisher()
        runner, occurrence, occurrences, lights, alarm, _ = make_runner(events=events)
        lights.list_rooms.return_value = [
            Room(
                id=ROOM_ID,
                name="Bedroom",
                scenes=(Scene(id=SCENE_ID, name="Nightlight", brightness=1),),
            )
        ]

        with patch("asyncio.sleep"):
            await runner.run(occurrence)

        assert occurrences.items[occurrence.id].state is OccurrenceState.DISMISSED
        assert alarm.defect is None
        assert events.of_type(AlarmUpdated) == []

    async def test_an_unreachable_bridge_is_not_blamed_on_the_alarm(self) -> None:
        events = RecordingPublisher()
        runner, occurrence, _, lights, alarm, _ = make_runner(events=events)
        lights.activate_scene.side_effect = RuntimeError("bridge unreachable")

        with patch("asyncio.sleep"):
            await runner.run(occurrence)

        assert alarm.defect is None
        assert events.of_type(AlarmUpdated) == []


class TestPublishedEvents:
    async def test_announces_the_sunrise_before_it_starts(self) -> None:
        events = RecordingPublisher()
        runner, occurrence, _, _, alarm, profile = make_runner(events=events)

        with patch("asyncio.sleep"):
            await runner.run(occurrence)

        started = events.only(OccurrenceStarted)
        assert started.label == alarm.label
        assert started.room_name == alarm.room_name
        assert started.sunrise_seconds == profile.sunrise_config.duration.seconds

    async def test_reports_progress_once_per_brightness_step(self) -> None:
        events = RecordingPublisher()
        runner, occurrence, _, lights, _, profile = make_runner(events=events)

        with patch("asyncio.sleep"):
            await runner.run(occurrence)

        progress = events.of_type(OccurrenceProgress)
        scene_brightness = round(
            (await lights.list_rooms())[0].scenes[0].brightness or 100
        )
        assert [event.brightness for event in progress] == [
            step.brightness
            for step in sunrise_steps(
                SunriseRamp(
                    duration=profile.sunrise_config.duration,
                    brightness_start=profile.sunrise_config.brightness_start,
                    brightness_end=scene_brightness,
                ),
                STEP,
            )
        ]
        assert progress[-1].percent == 100.0

    async def test_progress_stops_when_the_sunrise_is_interrupted(self) -> None:
        events = RecordingPublisher()
        runner, occurrence, occurrences, lights, _, _ = make_runner(events=events)

        async def dismiss_after_first_step(*args, **kwargs) -> None:
            stored = occurrences.items[occurrence.id]
            if stored.state is OccurrenceState.SUNRISE:
                stored.dismiss(NOW)

        lights.set_brightness.side_effect = dismiss_after_first_step

        with patch("asyncio.sleep"):
            await runner.run(occurrence)

        assert len(events.of_type(OccurrenceProgress)) == 1

    async def test_announces_the_finished_run(self) -> None:
        events = RecordingPublisher()
        runner, occurrence, _, _, _, _ = make_runner(events=events)

        with patch("asyncio.sleep"):
            await runner.run(occurrence)

        assert events.only(OccurrenceDismissed).occurrence.id == occurrence.id

    async def test_announces_a_failure_with_its_reason(self) -> None:
        """Anything that blows up outside the sunrise itself fails the run."""
        events = RecordingPublisher()
        runner, occurrence, _, _, _, _ = make_runner(events=events)

        class ExplodingProfiles(InMemoryProfileRepository):
            async def find_by_id(self, id):
                raise RuntimeError("database unavailable")

        runner._unit_of_work_factory.unit_of_work.profiles = ExplodingProfiles()

        with patch("asyncio.sleep"):
            await runner.run(occurrence)

        failed = events.only(OccurrenceFailed).occurrence
        assert "database unavailable" in (failed.failure_reason or "")
