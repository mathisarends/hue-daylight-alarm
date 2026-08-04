import asyncio
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

from huerise.features.alarm.domain import OccurrenceState, Weekday
from huerise.features.events.domain import OccurrenceScheduled, OccurrenceSkipped
from huerise.features.runner.application.runner_port import AlarmRunner
from huerise.features.scheduler.application import AlarmScheduler
from tests.application.conftest import (
    FakeUnitOfWork,
    FakeUnitOfWorkFactory,
    InMemoryAlarmRepository,
    InMemoryOccurrenceRepository,
    InMemoryProfileRepository,
    RecordingPublisher,
    make_alarm,
    make_occurrence,
    make_profile,
)

# 2026-08-03 is a Monday. 04:00 UTC == 06:00 Berlin.
NOW = datetime(2026, 8, 3, 4, 0, tzinfo=UTC)
SEVEN_BERLIN = datetime(2026, 8, 3, 5, 0, tzinfo=UTC)


def make_runner() -> AlarmRunner:
    runner = MagicMock(spec=AlarmRunner)
    runner.run = AsyncMock()
    return runner


def make_scheduler(
    alarms: InMemoryAlarmRepository | None = None,
    occurrences: InMemoryOccurrenceRepository | None = None,
    runner: AlarmRunner | None = None,
    events: RecordingPublisher | None = None,
) -> tuple[
    AlarmScheduler, InMemoryOccurrenceRepository, AlarmRunner, InMemoryAlarmRepository
]:
    alarms = alarms if alarms is not None else InMemoryAlarmRepository()
    occurrences = (
        occurrences if occurrences is not None else InMemoryOccurrenceRepository()
    )
    runner = runner if runner is not None else make_runner()
    unit_of_work = FakeUnitOfWork(
        alarms=alarms,
        profiles=InMemoryProfileRepository([make_profile()]),
        occurrences=occurrences,
    )
    scheduler = AlarmScheduler(
        unit_of_work_factory=FakeUnitOfWorkFactory(unit_of_work),
        runner=runner,
        events=events if events is not None else RecordingPublisher(),
    )
    return scheduler, occurrences, runner, alarms


class TestMaterialise:
    async def test_creates_the_next_occurrence_for_an_enabled_alarm(self) -> None:
        alarm = make_alarm(hour=7, minute=0)
        scheduler, occurrences, _, _ = make_scheduler(
            alarms=InMemoryAlarmRepository([alarm])
        )

        await scheduler.tick(NOW)

        created = list(occurrences.items.values())
        assert len(created) == 1
        assert created[0].scheduled_for == SEVEN_BERLIN

    async def test_is_idempotent_across_ticks(self) -> None:
        alarm = make_alarm(hour=7, minute=0)
        scheduler, occurrences, _, _ = make_scheduler(
            alarms=InMemoryAlarmRepository([alarm])
        )

        await scheduler.tick(NOW)
        await scheduler.tick(NOW + timedelta(minutes=1))

        assert len(occurrences.items) == 1

    async def test_ignores_disabled_alarms(self) -> None:
        alarm = make_alarm(hour=7, minute=0, is_enabled=False)
        scheduler, occurrences, _, _ = make_scheduler(
            alarms=InMemoryAlarmRepository([alarm])
        )

        await scheduler.tick(NOW)

        assert occurrences.items == {}

    async def test_ignores_alarms_beyond_the_lookahead(self) -> None:
        # Next Wednesday is more than 24h out from Monday 06:00 local.
        alarm = make_alarm(hour=7, minute=0, weekdays=frozenset({Weekday.WED}))
        scheduler, occurrences, _, _ = make_scheduler(
            alarms=InMemoryAlarmRepository([alarm])
        )

        await scheduler.tick(NOW)

        assert occurrences.items == {}


class TestDispatch:
    async def test_hands_a_due_occurrence_to_the_runner(self) -> None:
        alarm = make_alarm(hour=7, minute=0, weekdays=frozenset({Weekday.MON}))
        occurrence = make_occurrence(alarm.id, NOW)
        scheduler, occurrences, runner, _ = make_scheduler(
            alarms=InMemoryAlarmRepository([alarm]),
            occurrences=InMemoryOccurrenceRepository([occurrence]),
        )

        await scheduler.tick(NOW)
        await asyncio.sleep(0)  # let the spawned runner task start

        runner.run.assert_awaited_once()
        assert occurrences.items[occurrence.id].state is OccurrenceState.SUNRISE

    async def test_claims_the_occurrence_so_the_next_tick_skips_it(self) -> None:
        alarm = make_alarm(hour=7, minute=0, weekdays=frozenset({Weekday.MON}))
        occurrence = make_occurrence(alarm.id, NOW)
        scheduler, _, runner, _ = make_scheduler(
            alarms=InMemoryAlarmRepository([alarm]),
            occurrences=InMemoryOccurrenceRepository([occurrence]),
        )

        await scheduler.tick(NOW)
        await scheduler.tick(NOW + timedelta(seconds=30))
        await asyncio.sleep(0)

        assert runner.run.await_count == 1

    async def test_skips_an_occurrence_missed_beyond_the_grace_period(self) -> None:
        alarm = make_alarm(hour=7, minute=0, weekdays=frozenset({Weekday.MON}))
        occurrence = make_occurrence(alarm.id, NOW - timedelta(hours=3))
        scheduler, occurrences, runner, _ = make_scheduler(
            alarms=InMemoryAlarmRepository([alarm]),
            occurrences=InMemoryOccurrenceRepository([occurrence]),
        )

        await scheduler.tick(NOW)

        runner.run.assert_not_awaited()
        assert occurrences.items[occurrence.id].state is OccurrenceState.SKIPPED

    async def test_fires_a_snoozed_occurrence_again(self) -> None:
        alarm = make_alarm(hour=7, minute=0, weekdays=frozenset({Weekday.MON}))
        occurrence = make_occurrence(alarm.id, NOW, OccurrenceState.SNOOZED)
        scheduler, _, runner, _ = make_scheduler(
            alarms=InMemoryAlarmRepository([alarm]),
            occurrences=InMemoryOccurrenceRepository([occurrence]),
        )

        await scheduler.tick(NOW)
        await asyncio.sleep(0)

        runner.run.assert_awaited_once()

    async def test_one_time_alarm_disables_itself_when_it_fires(self) -> None:
        alarm = make_alarm(hour=7, minute=0)
        occurrence = make_occurrence(alarm.id, NOW)
        scheduler, _, _, alarms = make_scheduler(
            alarms=InMemoryAlarmRepository([alarm]),
            occurrences=InMemoryOccurrenceRepository([occurrence]),
        )

        await scheduler.tick(NOW)

        assert alarms.items[alarm.id].is_enabled is False

    async def test_recurring_alarm_stays_enabled(self) -> None:
        alarm = make_alarm(hour=7, minute=0, weekdays=frozenset({Weekday.MON}))
        occurrence = make_occurrence(alarm.id, NOW)
        scheduler, _, _, alarms = make_scheduler(
            alarms=InMemoryAlarmRepository([alarm]),
            occurrences=InMemoryOccurrenceRepository([occurrence]),
        )

        await scheduler.tick(NOW)

        assert alarms.items[alarm.id].is_enabled is True


class TestPublishedEvents:
    async def test_announces_a_newly_materialised_run(self) -> None:
        alarm = make_alarm(hour=7, minute=0)
        events = RecordingPublisher()
        scheduler, _, _, _ = make_scheduler(
            alarms=InMemoryAlarmRepository([alarm]), events=events
        )

        await scheduler.tick(NOW)

        scheduled = events.only(OccurrenceScheduled).occurrence
        assert scheduled.alarm_id == alarm.id
        assert scheduled.scheduled_for == SEVEN_BERLIN

    async def test_a_repeat_tick_announces_nothing_new(self) -> None:
        alarm = make_alarm(hour=7, minute=0)
        events = RecordingPublisher()
        scheduler, _, _, _ = make_scheduler(
            alarms=InMemoryAlarmRepository([alarm]), events=events
        )

        await scheduler.tick(NOW)
        await scheduler.tick(NOW)

        assert len(events.of_type(OccurrenceScheduled)) == 1

    async def test_announces_a_run_dropped_for_being_overdue(self) -> None:
        alarm = make_alarm(hour=7, minute=0)
        overdue = make_occurrence(alarm.id, NOW - timedelta(hours=1))
        events = RecordingPublisher()
        scheduler, _, _, _ = make_scheduler(
            alarms=InMemoryAlarmRepository([alarm]),
            occurrences=InMemoryOccurrenceRepository([overdue]),
            events=events,
        )

        await scheduler.tick(NOW)

        assert events.only(OccurrenceSkipped).occurrence.id == overdue.id
