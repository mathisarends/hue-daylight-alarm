from dishka import Provider, Scope, provide
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from huerise.features.alarm.application import (
    AlarmProfileService,
    AlarmService,
    LightReferenceSync,
)
from huerise.features.alarm.domain import (
    AlarmOccurrenceRepository,
    AlarmProfileRepository,
    AlarmRepository,
    AlarmUnitOfWorkFactory,
)
from huerise.features.alarm.infrastructure.persistence import (
    SQLAlarmOccurrenceRepository,
    SQLAlarmProfileRepository,
    SQLAlarmRepository,
    SQLAlarmUnitOfWorkFactory,
)
from huerise.features.devices.application import LightEvents, Lights
from huerise.features.events.application import EventPublisher


class AlarmProvider(Provider):
    scope = Scope.REQUEST

    @provide(scope=Scope.APP)
    def unit_of_work_factory(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> AlarmUnitOfWorkFactory:
        return SQLAlarmUnitOfWorkFactory(session_factory)

    @provide
    def alarm_repository(self, session: AsyncSession) -> AlarmRepository:
        return SQLAlarmRepository(session)

    @provide
    def profile_repository(self, session: AsyncSession) -> AlarmProfileRepository:
        return SQLAlarmProfileRepository(session)

    @provide
    def occurrence_repository(self, session: AsyncSession) -> AlarmOccurrenceRepository:
        return SQLAlarmOccurrenceRepository(session)

    @provide
    def alarm_service(
        self,
        alarms: AlarmRepository,
        profiles: AlarmProfileRepository,
        occurrences: AlarmOccurrenceRepository,
        lights: Lights,
        events: EventPublisher,
    ) -> AlarmService:
        return AlarmService(
            alarms=alarms,
            profiles=profiles,
            occurrences=occurrences,
            lights=lights,
            events=events,
        )

    @provide
    def profile_service(self, profiles: AlarmProfileRepository) -> AlarmProfileService:
        return AlarmProfileService(profiles)

    @provide(scope=Scope.APP)
    def light_reference_sync(
        self,
        light_events: LightEvents,
        lights: Lights,
        unit_of_work_factory: AlarmUnitOfWorkFactory,
        publisher: EventPublisher,
    ) -> LightReferenceSync:
        return LightReferenceSync(
            events=light_events,
            lights=lights,
            unit_of_work_factory=unit_of_work_factory,
            publisher=publisher,
        )
