from collections.abc import Iterator

from dishka import Provider, Scope, alias, provide
from transitbus import EventBus

from huerise.features.events.application import EventPublisher, EventStreamHub

# How many events stay available for replay to a reconnecting client. One
# wake-up costs roughly 80, so this covers a good many of them.
MAX_HISTORY = 1000


class EventsProvider(Provider):
    scope = Scope.APP

    @provide
    def event_bus(self) -> EventBus:
        return EventBus(name="huerise", max_history=MAX_HISTORY)

    @provide
    def event_stream_hub(self, bus: EventBus) -> Iterator[EventStreamHub]:
        hub = EventStreamHub(bus)
        yield hub
        hub.close()

    publisher = alias(source=EventStreamHub, provides=EventPublisher)
