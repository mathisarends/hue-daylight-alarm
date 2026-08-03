from abc import ABC, abstractmethod

from huerise.features.alarm.domain import Alarm


class AlarmRunner(ABC):
    @abstractmethod
    async def run(self, alarm: Alarm) -> None: ...
