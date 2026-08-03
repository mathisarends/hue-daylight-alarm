from abc import ABC, abstractmethod
from types import TracebackType
from typing import Self

from huerise.features.alarm.domain.repository import (
    AlarmOccurrenceRepository,
    AlarmProfileRepository,
    AlarmRepository,
)


class AlarmUnitOfWork(ABC):
    """One transaction over all alarm repositories.

    Background work (scheduler, runner) cannot share the request-scoped
    session, so it opens a unit of work per step instead.
    """

    alarms: AlarmRepository
    profiles: AlarmProfileRepository
    occurrences: AlarmOccurrenceRepository

    @abstractmethod
    async def __aenter__(self) -> Self: ...

    @abstractmethod
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None: ...


class AlarmUnitOfWorkFactory(ABC):
    @abstractmethod
    def create(self) -> AlarmUnitOfWork: ...
