import asyncio
import logging
from datetime import UTC, datetime, timedelta

from huerise.features.alarm.domain import (
    AlarmOccurrence,
    AlarmUnitOfWork,
    AlarmUnitOfWorkFactory,
)
from huerise.features.events.application import EventPublisher
from huerise.features.events.domain import (
    OccurrenceScheduled,
    OccurrenceSkipped,
    OccurrenceSnapshot,
)
from huerise.features.runner.application.runner_port import AlarmRunner
from huerise.lifecycle import Runnable

logger = logging.getLogger(__name__)

_TICK_INTERVAL = timedelta(seconds=30)
# How far ahead occurrences are materialised. One day is enough to see every
# rule at least once while keeping the table small.
_LOOKAHEAD = timedelta(hours=24)
# An occurrence missed by more than this (process was down) is skipped rather
# than fired hours late.
_GRACE_PERIOD = timedelta(minutes=15)


class AlarmScheduler(Runnable):
    """Turns alarm rules into occurrences and hands due ones to the runner."""

    def __init__(
        self,
        unit_of_work_factory: AlarmUnitOfWorkFactory,
        runner: AlarmRunner,
        events: EventPublisher,
        tick_interval: timedelta = _TICK_INTERVAL,
        lookahead: timedelta = _LOOKAHEAD,
        grace_period: timedelta = _GRACE_PERIOD,
    ) -> None:
        self._unit_of_work_factory = unit_of_work_factory
        self._runner = runner
        self._events = events
        self._tick_interval = tick_interval
        self._lookahead = lookahead
        self._grace_period = grace_period
        self._running_tasks: set[asyncio.Task[None]] = set()
        self._task: asyncio.Task[None] | None = None

    async def start(self) -> None:
        self._task = asyncio.create_task(self.run())

    async def stop(self) -> None:
        if self._task is None:
            return
        self._task.cancel()
        try:
            await self._task
        except asyncio.CancelledError:
            pass
        finally:
            self._task = None

    async def run(self) -> None:
        while True:
            try:
                await self.tick()
            except Exception:
                logger.exception("Scheduler tick failed")
            await asyncio.sleep(self._tick_interval.total_seconds())

    async def tick(self, now: datetime | None = None) -> None:
        now = now or datetime.now(UTC)
        await self._materialise(now)
        for occurrence in await self._claim_due(now):
            self._spawn(occurrence)

    async def _materialise(self, now: datetime) -> None:
        """Create the next pending occurrence for every enabled alarm.

        Idempotent: the unique constraint on (alarm_id, scheduled_for) means a
        restart mid-day cannot produce a duplicate run.
        """
        async with self._unit_of_work_factory.create() as uow:
            for alarm in await uow.alarms.find_enabled():
                scheduled_for = alarm.next_occurrence(now)
                if scheduled_for is None or scheduled_for - now > self._lookahead:
                    continue
                created = await uow.occurrences.ensure_scheduled(
                    alarm.id, scheduled_for
                )
                if created is not None:
                    logger.info(
                        "Scheduled '%s' for %s", alarm.label, scheduled_for.isoformat()
                    )
                    self._events.publish(
                        OccurrenceScheduled(
                            occurrence=OccurrenceSnapshot.from_domain(created)
                        )
                    )

    async def _claim_due(self, now: datetime) -> list[AlarmOccurrence]:
        """Move due occurrences into SUNRISE so a later tick cannot re-fire them."""
        claimed: list[AlarmOccurrence] = []

        async with self._unit_of_work_factory.create() as uow:
            for occurrence in await uow.occurrences.find_due(now):
                if occurrence.scheduled_for < now - self._grace_period:
                    logger.warning(
                        "Skipping occurrence %s, overdue since %s",
                        occurrence.id,
                        occurrence.scheduled_for.isoformat(),
                    )
                    occurrence.skip(now)
                    await uow.occurrences.save(occurrence)
                    self._events.publish(
                        OccurrenceSkipped(
                            occurrence=OccurrenceSnapshot.from_domain(occurrence)
                        )
                    )
                    continue

                occurrence.start_sunrise(now)
                await uow.occurrences.save(occurrence)
                await _retire_one_time_alarm(uow, occurrence)
                claimed.append(occurrence)

        return claimed

    def _spawn(self, occurrence: AlarmOccurrence) -> None:
        task = asyncio.create_task(self._runner.run(occurrence))
        self._running_tasks.add(task)
        task.add_done_callback(self._running_tasks.discard)


async def _retire_one_time_alarm(
    uow: AlarmUnitOfWork, occurrence: AlarmOccurrence
) -> None:
    alarm = await uow.alarms.find_by_id(occurrence.alarm_id)
    if alarm is None or alarm.schedule.is_recurring or not alarm.is_enabled:
        return
    alarm.disable()
    await uow.alarms.save(alarm)
