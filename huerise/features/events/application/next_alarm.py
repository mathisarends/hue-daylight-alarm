import logging
from datetime import datetime
from uuid import UUID

from transitbus import EventBus

from huerise.features.alarm.domain import Alarm, AlarmUnitOfWorkFactory
from huerise.features.events.domain import (
    AlarmCreated,
    AlarmDeleted,
    AlarmSnapshot,
    AlarmUpdated,
    HueriseEvent,
    NextAlarmChanged,
    OccurrenceStarted,
)

logger = logging.getLogger(__name__)

type Upcoming = tuple[Alarm, datetime]


class NextAlarmTracker:
    """Derives `alarm.next_changed` so that nobody has to emit it by hand.

    Listens for the events that can move the next wake-up, recomputes it, and
    publishes only on a real difference. Dispatching from inside a handler
    makes transitbus record the triggering event as `parent_id`, so a client
    sees which change caused the new next alarm.
    """

    # Sunrise progress is deliberately absent: it fires once per brightness
    # step and cannot move a rule, so reacting to it would mean a database
    # round trip every few seconds for nothing.
    TRIGGERS: tuple[type[HueriseEvent], ...] = (
        AlarmCreated,
        AlarmUpdated,
        AlarmDeleted,
        OccurrenceStarted,
    )

    def __init__(
        self, bus: EventBus, unit_of_work_factory: AlarmUnitOfWorkFactory
    ) -> None:
        self._bus = bus
        self._unit_of_work_factory = unit_of_work_factory
        self._current: tuple[UUID, datetime] | None = None

        for trigger in self.TRIGGERS:
            self._bus.on(trigger, self._on_trigger)

    async def start(self) -> None:
        """Take the baseline, so that the first change published is a real one."""
        self._current = _key(await self._earliest())
        logger.info("Tracking next alarm from %s", _describe(self._current))

    async def _on_trigger(self, event: HueriseEvent) -> None:
        upcoming = await self._earliest()
        key = _key(upcoming)
        if key == self._current:
            return

        self._current = key
        logger.info("Next alarm is now %s", _describe(key))
        self._bus.dispatch(
            NextAlarmChanged(
                alarm=AlarmSnapshot.from_domain(upcoming[0]) if upcoming else None,
                scheduled_for=upcoming[1] if upcoming else None,
            )
        )

    async def _earliest(self) -> Upcoming | None:
        async with self._unit_of_work_factory.create() as uow:
            alarms = await uow.alarms.find_enabled()

        upcoming = [
            (alarm, when)
            for alarm in alarms
            if (when := alarm.next_occurrence()) is not None
        ]
        return min(upcoming, key=lambda candidate: candidate[1], default=None)


def _key(upcoming: Upcoming | None) -> tuple[UUID, datetime] | None:
    """What counts as a change: which alarm is next, and when it fires."""
    if upcoming is None:
        return None
    alarm, scheduled_for = upcoming
    return alarm.id, scheduled_for


def _describe(key: tuple[UUID, datetime] | None) -> str:
    return key[1].isoformat() if key else "nothing"
