from types import TracebackType

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from huerise.features.alarm.domain.unit_of_work import (
    AlarmUnitOfWork,
    AlarmUnitOfWorkFactory,
)
from huerise.features.alarm.infrastructure.persistence.repository import (
    SQLAlarmOccurrenceRepository,
    SQLAlarmProfileRepository,
    SQLAlarmRepository,
)


class SQLAlarmUnitOfWork(AlarmUnitOfWork):
    """Owns one session for the duration of the ``async with`` block."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory
        self._session: AsyncSession | None = None

    async def __aenter__(self) -> SQLAlarmUnitOfWork:
        self._session = self._session_factory()
        self.alarms = SQLAlarmRepository(self._session)
        self.profiles = SQLAlarmProfileRepository(self._session)
        self.occurrences = SQLAlarmOccurrenceRepository(self._session)
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        session = self._session
        if session is None:
            return
        try:
            if exc_type is None:
                await session.commit()
            else:
                await session.rollback()
        finally:
            await session.close()
            self._session = None


class SQLAlarmUnitOfWorkFactory(AlarmUnitOfWorkFactory):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    def create(self) -> AlarmUnitOfWork:
        return SQLAlarmUnitOfWork(self._session_factory)
