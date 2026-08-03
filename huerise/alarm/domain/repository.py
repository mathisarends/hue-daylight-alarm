import uuid
from abc import ABC, abstractmethod
from collections.abc import Sequence

from huerise.alarm.domain.alarm import Alarm


class AlarmRepository(ABC):
    @abstractmethod
    async def get(self, alarm_id: uuid.UUID) -> Alarm | None: ...

    @abstractmethod
    async def get_all(self) -> Sequence[Alarm]: ...

    @abstractmethod
    async def get_scheduled(self) -> Sequence[Alarm]: ...

    @abstractmethod
    async def save(self, alarm: Alarm) -> Alarm: ...

    @abstractmethod
    async def delete(self, alarm_id: uuid.UUID) -> None: ...
