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
    IntroSettings,
    OccurrenceState,
    RingtoneSettings,
    Schedule,
    SunriseSettings,
    Weekday,
)
from huerise.features.devices.application import AudioPlayer, Lights
from huerise.infrastructure.storage import StorageBackend, StorageFile, UploadResponse
from huerise.infrastructure.storage.port import DEFAULT_LINK_LIFETIME

BERLIN = ZoneInfo("Europe/Berlin")


class FakeStorage(StorageBackend):
    """Object storage holding nothing but the keys it was handed."""

    def __init__(self, paths: list[str]) -> None:
        self.paths = paths
        self.list_calls = 0

    async def list_files(self, path: str = "") -> list[StorageFile]:
        self.list_calls += 1
        return [
            StorageFile(name=p.rsplit("/", maxsplit=1)[-1], storage_path=p)
            for p in self.paths
            if p.startswith(path)
        ]

    async def download_bytes(self, path: str) -> bytes:
        raise NotImplementedError

    async def upload_bytes(
        self, path: str, data: bytes, content_type: str | None = None
    ) -> UploadResponse:
        raise NotImplementedError

    async def public_url(
        self, path: str, lifetime: timedelta = DEFAULT_LINK_LIFETIME
    ) -> str:
        return f"https://storage.test/{path}"


def make_sound_storage() -> FakeStorage:
    return FakeStorage(
        [
            "wake_up_sounds/wake-up-bowls.mp3",
            "wake_up_sounds/wake-up-mist.mp3",
            "get_up_sounds/get-up-aurora.mp3",
        ]
    )


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

    async def __aenter__(self) -> "FakeUnitOfWork":
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
        intro_settings=IntroSettings(
            sound_id=UUID("1693baba-146e-5b14-acf2-6f76554f36e9")
        ),
        sunrise_settings=SunriseSettings(duration=sunrise_duration),
        ringtone_settings=RingtoneSettings(
            sound_id=UUID("5c0806e7-7162-5be7-948e-33d349bde4a8")
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
        room_name="Bedroom",
        is_enabled=is_enabled,
    )


def make_occurrence(
    alarm_id: UUID,
    scheduled_for: datetime,
    state: OccurrenceState = OccurrenceState.PENDING,
) -> AlarmOccurrence:
    return AlarmOccurrence(alarm_id=alarm_id, scheduled_for=scheduled_for, state=state)


def make_audio() -> AudioPlayer:
    audio = MagicMock(spec=AudioPlayer)
    audio.play = AsyncMock()
    audio.stop = AsyncMock()
    audio.set_volume = AsyncMock()
    return audio


def make_lights() -> Lights:
    lights = MagicMock(spec=Lights)
    lights.list_rooms = AsyncMock(return_value=[])
    lights.activate_scene = AsyncMock()
    lights.set_brightness = AsyncMock()
    return lights


def make_alarm_service(
    alarms: AlarmRepository | None = None,
    profiles: AlarmProfileRepository | None = None,
    occurrences: AlarmOccurrenceRepository | None = None,
    audio: AudioPlayer | None = None,
) -> AlarmService:
    return AlarmService(
        alarms=alarms if alarms is not None else InMemoryAlarmRepository(),
        profiles=profiles
        if profiles is not None
        else InMemoryProfileRepository([make_profile()]),
        occurrences=occurrences
        if occurrences is not None
        else InMemoryOccurrenceRepository(),
        audio=audio if audio is not None else make_audio(),
    )
