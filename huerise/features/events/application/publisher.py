from typing import Protocol

from huerise.features.events.domain import HueriseEvent


class EventPublisher(Protocol):
    """All the rest of the app sees of the stream: somewhere to drop an event.

    Deliberately synchronous. Emitting is fire-and-forget, so a stalled or
    absent listener can never delay -- let alone fail -- an alarm.
    """

    def publish(self, event: HueriseEvent) -> None: ...
