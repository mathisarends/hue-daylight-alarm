from abc import ABC, abstractmethod
from datetime import datetime
from uuid import UUID

from huerise.features.alarm.domain.alarm import Alarm
from huerise.features.alarm.domain.occurrence import AlarmOccurrence
from huerise.features.alarm.domain.profile import AlarmProfile


class AlarmRepository(ABC):
    @abstractmethod
    async def find_by_id(self, id: UUID) -> Alarm | None: ...

    @abstractmethod
    async def find_all(self) -> list[Alarm]: ...

    @abstractmethod
    async def find_enabled(self) -> list[Alarm]: ...

    @abstractmethod
    async def save(self, domain: Alarm) -> Alarm: ...

    @abstractmethod
    async def delete_by_id(self, id: UUID) -> bool: ...


class AlarmProfileRepository(ABC):
    @abstractmethod
    async def find_by_id(self, id: UUID) -> AlarmProfile | None: ...

    @abstractmethod
    async def find_all(self) -> list[AlarmProfile]: ...

    @abstractmethod
    async def find_default(self) -> AlarmProfile | None: ...

    @abstractmethod
    async def save(self, domain: AlarmProfile) -> AlarmProfile: ...


class AlarmOccurrenceRepository(ABC):
    @abstractmethod
    async def find_by_id(self, id: UUID) -> AlarmOccurrence | None: ...

    @abstractmethod
    async def find_for_alarm(
        self, alarm_id: UUID, limit: int = 20
    ) -> list[AlarmOccurrence]: ...

    @abstractmethod
    async def find_active_for_alarm(self, alarm_id: UUID) -> AlarmOccurrence | None:
        """The occurrence currently running or snoozed for this alarm."""

    @abstractmethod
    async def find_due(self, now: datetime) -> list[AlarmOccurrence]:
        """Waiting occurrences whose scheduled time has passed."""

    @abstractmethod
    async def ensure_scheduled(
        self, alarm_id: UUID, scheduled_for: datetime
    ) -> AlarmOccurrence | None:
        """Materialise a pending occurrence; None if that slot already exists."""

    @abstractmethod
    async def save(self, domain: AlarmOccurrence) -> AlarmOccurrence: ...
