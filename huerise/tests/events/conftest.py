from collections.abc import AsyncIterator

from transitbus import EventBus

from huerise.features.events.application import EventStreamHub
from huerise.features.events.domain import AlarmCreated, AlarmSnapshot, HueriseEvent
from huerise.tests.application.conftest import make_alarm


def make_hub(max_pending: int = 10) -> tuple[EventBus, EventStreamHub]:
    bus = EventBus(name="test", max_history=100)
    return bus, EventStreamHub(bus, max_pending=max_pending)


def make_created() -> AlarmCreated:
    return AlarmCreated(alarm=AlarmSnapshot.from_domain(make_alarm()))


async def take(stream: AsyncIterator[HueriseEvent], count: int) -> list[HueriseEvent]:
    return [await anext(stream) for _ in range(count)]
