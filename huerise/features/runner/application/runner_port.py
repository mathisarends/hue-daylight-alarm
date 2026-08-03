from abc import ABC, abstractmethod

from huerise.features.alarm.domain import AlarmOccurrence


class AlarmRunner(ABC):
    @abstractmethod
    async def run(self, occurrence: AlarmOccurrence) -> None: ...
