import asyncio
from datetime import UTC, datetime

from transitbus import EventBus

from huerise.features.alarm.domain import Alarm, AlarmField
from huerise.features.events.application import NextAlarmTracker
from huerise.features.events.domain import (
    AlarmCreated,
    AlarmDeleted,
    AlarmSnapshot,
    AlarmUpdated,
    HueriseEvent,
    NextAlarmChanged,
    OccurrenceProgress,
    OccurrenceSnapshot,
    OccurrenceStarted,
)
from tests.application.conftest import (
    FakeUnitOfWork,
    FakeUnitOfWorkFactory,
    InMemoryAlarmRepository,
    InMemoryOccurrenceRepository,
    InMemoryProfileRepository,
    make_alarm,
    make_occurrence,
    make_profile,
)

NOW = datetime(2026, 8, 3, 4, 0, tzinfo=UTC)


async def make_tracker(
    *alarms: Alarm,
) -> tuple[EventBus, InMemoryAlarmRepository, NextAlarmTracker]:
    repository = InMemoryAlarmRepository(list(alarms))
    unit_of_work = FakeUnitOfWork(
        alarms=repository,
        profiles=InMemoryProfileRepository([make_profile()]),
        occurrences=InMemoryOccurrenceRepository(),
    )
    bus = EventBus(name="test", max_history=100)
    tracker = NextAlarmTracker(bus, FakeUnitOfWorkFactory(unit_of_work))
    await tracker.start()
    return bus, repository, tracker


async def settle(bus: EventBus) -> None:
    """Drain the bus, including events dispatched from inside a handler."""
    for _ in range(3):
        await bus.idle()
        await asyncio.sleep(0)


def derived(bus: EventBus) -> list[NextAlarmChanged]:
    return [event for event in bus.history if isinstance(event, NextAlarmChanged)]


async def announce(bus: EventBus, event: HueriseEvent) -> None:
    bus.dispatch(event)
    await settle(bus)


async def test_a_new_earlier_alarm_becomes_the_next_one() -> None:
    later = make_alarm(hour=9, minute=0)
    bus, repository, _ = await make_tracker(later)

    earlier = make_alarm(hour=6, minute=0)
    await repository.save(earlier)
    await announce(bus, AlarmCreated(alarm=AlarmSnapshot.from_domain(earlier)))

    published = derived(bus)
    assert len(published) == 1
    assert published[0].alarm is not None
    assert published[0].alarm.id == earlier.id
    assert published[0].scheduled_for == earlier.next_occurrence()


async def test_a_new_later_alarm_leaves_the_next_one_alone() -> None:
    earlier = make_alarm(hour=6, minute=0)
    bus, repository, _ = await make_tracker(earlier)

    later = make_alarm(hour=9, minute=0)
    await repository.save(later)
    await announce(bus, AlarmCreated(alarm=AlarmSnapshot.from_domain(later)))

    assert derived(bus) == []


async def test_removing_the_last_alarm_reports_nothing_upcoming() -> None:
    alarm = make_alarm(hour=6, minute=0)
    bus, repository, _ = await make_tracker(alarm)

    await repository.delete_by_id(alarm.id)
    await announce(bus, AlarmDeleted(alarm_id=alarm.id))

    published = derived(bus)
    assert len(published) == 1
    assert published[0].alarm is None
    assert published[0].scheduled_for is None


async def test_the_cause_of_the_change_is_recorded() -> None:
    bus, repository, _ = await make_tracker()

    alarm = make_alarm(hour=6, minute=0)
    await repository.save(alarm)
    cause = AlarmCreated(alarm=AlarmSnapshot.from_domain(alarm))
    await announce(bus, cause)

    assert derived(bus)[0].parent_id == cause.id


async def test_sunrise_progress_is_not_a_trigger() -> None:
    alarm = make_alarm(hour=6, minute=0)
    bus, repository, _ = await make_tracker(alarm)

    # A change the tracker would pick up, announced by an event it ignores.
    await repository.delete_by_id(alarm.id)
    await announce(
        bus,
        OccurrenceProgress(
            occurrence_id=alarm.id,
            alarm_id=alarm.id,
            brightness=42,
            step=3,
            total_steps=70,
            elapsed_seconds=18,
            total_seconds=420,
        ),
    )

    assert derived(bus) == []


async def test_the_same_change_is_announced_once() -> None:
    later = make_alarm(hour=9, minute=0)
    bus, repository, _ = await make_tracker(later)

    earlier = make_alarm(hour=6, minute=0)
    await repository.save(earlier)
    created = AlarmSnapshot.from_domain(earlier)
    await announce(bus, AlarmCreated(alarm=created))
    await announce(bus, AlarmCreated(alarm=created))

    assert len(derived(bus)) == 1


async def test_a_started_run_is_a_trigger() -> None:
    """A one-time alarm retires as it fires, which moves the next wake-up."""
    firing = make_alarm(hour=6, minute=0)
    later = make_alarm(hour=9, minute=0)
    bus, repository, _ = await make_tracker(firing, later)

    firing.disable()
    await repository.save(firing)
    await announce(
        bus,
        OccurrenceStarted(
            occurrence=OccurrenceSnapshot.from_domain(
                make_occurrence(firing.id, firing.schedule.next_occurrence(NOW))
            ),
            label=firing.label,
            room_name=firing.room_name,
            sunrise_seconds=420,
        ),
    )

    published = derived(bus)
    assert len(published) == 1
    assert published[0].alarm is not None
    assert published[0].alarm.id == later.id


async def test_disabling_the_next_alarm_promotes_the_one_behind_it() -> None:
    earlier = make_alarm(hour=6, minute=0)
    later = make_alarm(hour=9, minute=0)
    bus, repository, _ = await make_tracker(earlier, later)

    earlier.disable()
    await repository.save(earlier)
    await announce(
        bus,
        AlarmUpdated(
            alarm=AlarmSnapshot.from_domain(earlier), changed=[AlarmField.IS_ENABLED]
        ),
    )

    published = derived(bus)
    assert len(published) == 1
    assert published[0].alarm is not None
    assert published[0].alarm.id == later.id
