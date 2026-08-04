from dishka import Provider, Scope, make_async_container, provide

from huerise.features.alarm.domain import AlarmUnitOfWorkFactory
from huerise.features.events.application import (
    EventPublisher,
    EventStreamHub,
    NextAlarmTracker,
)
from huerise.features.events.domain import NextAlarmChanged
from huerise.features.events.infrastructure import EventsProvider
from tests.application.conftest import (
    FakeUnitOfWork,
    FakeUnitOfWorkFactory,
    InMemoryAlarmRepository,
    InMemoryOccurrenceRepository,
    InMemoryProfileRepository,
    make_alarm,
)
from tests.events.conftest import make_created


class StubUnitOfWorkProvider(Provider):
    scope = Scope.APP

    def __init__(self, alarms: InMemoryAlarmRepository) -> None:
        super().__init__()
        self._alarms = alarms

    @provide
    def unit_of_work_factory(self) -> AlarmUnitOfWorkFactory:
        return FakeUnitOfWorkFactory(
            FakeUnitOfWork(
                alarms=self._alarms,
                profiles=InMemoryProfileRepository(),
                occurrences=InMemoryOccurrenceRepository(),
            )
        )


def make_container(alarms: InMemoryAlarmRepository | None = None):
    return make_async_container(
        EventsProvider(),
        StubUnitOfWorkProvider(alarms or InMemoryAlarmRepository()),
    )


async def test_the_publisher_is_the_hub() -> None:
    async with make_container() as container:
        hub = await container.get(EventStreamHub)

        assert await container.get(EventPublisher) is hub


async def test_the_tracker_listens_on_the_bus_the_hub_serves() -> None:
    """On separate buses the tracker would never see what the app publishes."""
    alarms = InMemoryAlarmRepository([make_alarm(hour=6, minute=0)])

    async with make_container(alarms) as container:
        hub = await container.get(EventStreamHub)
        tracker = await container.get(NextAlarmTracker)
        await tracker.start()

        async with hub.subscribe() as stream:
            await alarms.save(make_alarm(hour=5, minute=0))
            hub.publish(make_created())

            await anext(stream)
            assert isinstance(await anext(stream), NextAlarmChanged)
