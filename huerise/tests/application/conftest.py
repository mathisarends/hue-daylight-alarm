from datetime import datetime, timedelta
from types import TracebackType
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

from huerise.features.alarm.application import AlarmService
from huerise.features.alarm.domain import (
    Alarm,
    AlarmOccurrence,
    AlarmOccurrenceRepository,
    AlarmProfile,
    AlarmProfileRepository,
    AlarmRepository,
    AlarmUnitOfWork,
    AlarmUnitOfWorkFactory,
    OccurrenceState,
    Schedule,
    SunriseConfig,
    Weekday,
)
from huerise.features.events.application import EventPublisher
from huerise.features.events.domain import HueriseEvent
from huerise.features.lighting.application import Lights
from huerise.features.lighting.domain import Room, Scene

BERLIN = ZoneInfo("Europe/Berlin")
ROOM_ID = UUID("11111111-1111-4111-8111-111111111111")
SCENE_ID = UUID("22222222-2222-4222-8222-222222222222")


class InMemoryAlarmRepository(AlarmRepository):
    def __init__(self, alarms: list[Alarm] | None = None) -> None:
        self.items: dict[UUID, Alarm] = {a.id: a for a in alarms or []}

    async def find_by_id(self, id: UUID) -> Alarm | None:
        return self.items.get(id)

    async def find_all(self) -> list[Alarm]:
        return list(self.items.values())

    async def find_enabled(self) -> list[Alarm]:
        return [a for a in self.items.values() if a.is_enabled]

    async def save(self, domain: Alarm) -> Alarm:
        self.items[domain.id] = domain
        return domain

    async def delete_by_id(self, id: UUID) -> bool:
        return self.items.pop(id, None) is not None


class InMemoryProfileRepository(AlarmProfileRepository):
    def __init__(self, profiles: list[AlarmProfile] | None = None) -> None:
        self.items: dict[UUID, AlarmProfile] = {p.id: p for p in profiles or []}

    async def find_by_id(self, id: UUID) -> AlarmProfile | None:
        return self.items.get(id)

    async def find_all(self) -> list[AlarmProfile]:
        return list(self.items.values())

    async def find_default(self) -> AlarmProfile | None:
        return next((p for p in self.items.values() if p.is_default), None)

    async def save(self, domain: AlarmProfile) -> AlarmProfile:
        self.items[domain.id] = domain
        return domain

    async def delete_by_id(self, id: UUID) -> bool:
        return self.items.pop(id, None) is not None


class InMemoryOccurrenceRepository(AlarmOccurrenceRepository):
    def __init__(self, occurrences: list[AlarmOccurrence] | None = None) -> None:
        self.items: dict[UUID, AlarmOccurrence] = {o.id: o for o in occurrences or []}

    async def find_by_id(self, id: UUID) -> AlarmOccurrence | None:
        return self.items.get(id)

    async def find_for_alarm(
        self, alarm_id: UUID, limit: int = 20
    ) -> list[AlarmOccurrence]:
        matches = [o for o in self.items.values() if o.alarm_id == alarm_id]
        return sorted(matches, key=lambda o: o.scheduled_for, reverse=True)[:limit]

    async def find_active_for_alarm(self, alarm_id: UUID) -> AlarmOccurrence | None:
        matches = [
            o
            for o in self.items.values()
            if o.alarm_id == alarm_id and not o.is_finished
        ]
        return max(matches, key=lambda o: o.scheduled_for, default=None)

    async def find_due(self, now: datetime) -> list[AlarmOccurrence]:
        due = [o for o in self.items.values() if o.is_due(now)]
        return sorted(due, key=lambda o: o.scheduled_for)

    async def ensure_scheduled(
        self, alarm_id: UUID, scheduled_for: datetime
    ) -> AlarmOccurrence | None:
        exists = any(
            o.alarm_id == alarm_id and o.scheduled_for == scheduled_for
            for o in self.items.values()
        )
        if exists:
            return None
        occurrence = AlarmOccurrence(alarm_id=alarm_id, scheduled_for=scheduled_for)
        self.items[occurrence.id] = occurrence
        return occurrence

    async def save(self, domain: AlarmOccurrence) -> AlarmOccurrence:
        self.items[domain.id] = domain
        return domain


class FakeUnitOfWork(AlarmUnitOfWork):
    """Shares one set of in-memory repositories across every block."""

    def __init__(
        self,
        alarms: AlarmRepository,
        profiles: AlarmProfileRepository,
        occurrences: AlarmOccurrenceRepository,
    ) -> None:
        self.alarms = alarms
        self.profiles = profiles
        self.occurrences = occurrences

    async def __aenter__(self) -> FakeUnitOfWork:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        return None


class FakeUnitOfWorkFactory(AlarmUnitOfWorkFactory):
    def __init__(self, unit_of_work: FakeUnitOfWork) -> None:
        self.unit_of_work = unit_of_work

    def create(self) -> AlarmUnitOfWork:
        return self.unit_of_work


def make_profile(
    name: str = "Standard",
    is_default: bool = True,
    sunrise_duration: timedelta = timedelta(minutes=7),
) -> AlarmProfile:
    return AlarmProfile(
        name=name,
        is_default=is_default,
        sunrise_config=SunriseConfig(
            scene_id=SCENE_ID,
            scene_name="Tageslichtwecker",
            duration=sunrise_duration,
        ),
    )


def make_alarm(
    hour: int = 7,
    minute: int = 0,
    weekdays: frozenset[Weekday] = frozenset(),
    is_enabled: bool = True,
    profile_id: UUID | None = None,
    tz: ZoneInfo = BERLIN,
) -> Alarm:
    return Alarm(
        label="Morning",
        schedule=Schedule(hour=hour, minute=minute, tz=tz, weekdays=weekdays),
        profile_id=profile_id or uuid4(),
        room_id=ROOM_ID,
        room_name="Bedroom",
        is_enabled=is_enabled,
    )


def make_occurrence(
    alarm_id: UUID,
    scheduled_for: datetime,
    state: OccurrenceState = OccurrenceState.PENDING,
) -> AlarmOccurrence:
    return AlarmOccurrence(alarm_id=alarm_id, scheduled_for=scheduled_for, state=state)


def make_lights() -> Lights:
    lights = MagicMock(spec=Lights)
    lights.list_rooms = AsyncMock(
        return_value=[
            Room(
                id=ROOM_ID,
                name="Bedroom",
                scenes=(
                    Scene(
                        id=SCENE_ID,
                        name="Tageslichtwecker",
                        brightness=72,
                    ),
                ),
            )
        ]
    )
    lights.activate_scene = AsyncMock()
    lights.set_brightness = AsyncMock()
    return lights


class RecordingPublisher(EventPublisher):
    """Keeps what was published, so a test can assert on the stream."""

    def __init__(self) -> None:
        self.events: list[HueriseEvent] = []

    def publish(self, event: HueriseEvent) -> None:
        self.events.append(event)

    def of_type[E: HueriseEvent](self, event_type: type[E]) -> list[E]:
        return [event for event in self.events if isinstance(event, event_type)]

    def only[E: HueriseEvent](self, event_type: type[E]) -> E:
        published = self.of_type(event_type)
        assert len(published) == 1, (
            f"expected exactly one {event_type.__name__}, got {len(published)}"
        )
        return published[0]


def make_alarm_service(
    alarms: AlarmRepository | None = None,
    profiles: AlarmProfileRepository | None = None,
    occurrences: AlarmOccurrenceRepository | None = None,
    lights: Lights | None = None,
    events: EventPublisher | None = None,
) -> AlarmService:
    return AlarmService(
        alarms=alarms if alarms is not None else InMemoryAlarmRepository(),
        profiles=profiles
        if profiles is not None
        else InMemoryProfileRepository([make_profile()]),
        occurrences=occurrences
        if occurrences is not None
        else InMemoryOccurrenceRepository(),
        lights=lights if lights is not None else make_lights(),
        events=events if events is not None else RecordingPublisher(),
    )
