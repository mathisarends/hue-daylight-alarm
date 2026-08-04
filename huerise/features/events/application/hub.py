import asyncio
import logging
from collections.abc import AsyncGenerator, AsyncIterator, Iterable
from contextlib import asynccontextmanager

from transitbus import EventBus

from huerise.features.events.domain import HueriseEvent

logger = logging.getLogger(__name__)

# A client further behind than this is cut loose rather than slowing the bus.
MAX_PENDING_PER_CLIENT = 200


class _Subscription:
    """One attached client: a replay backlog, then a bounded live queue.

    The backlog is kept apart from the queue so that a long replay cannot
    itself trip the overflow guard.
    """

    __slots__ = ("_backlog", "_closed", "_queue")

    def __init__(self, backlog: Iterable[HueriseEvent], max_pending: int) -> None:
        self._backlog = list(backlog)
        self._queue: asyncio.Queue[HueriseEvent | None] = asyncio.Queue(max_pending)
        self._closed = False

    def offer(self, event: HueriseEvent) -> None:
        if self._closed:
            return
        try:
            self._queue.put_nowait(event)
        except asyncio.QueueFull:
            logger.warning("Event stream client fell behind, dropping it")
            self.close()

    def close(self) -> None:
        """End the stream, discarding whatever is still queued.

        A client that fell behind gets nothing rather than a stale burst. It
        reconnects, and its `Last-Event-ID` is by then too old to replay --
        exactly the signal to resync over REST.
        """
        if self._closed:
            return
        self._closed = True
        while not self._queue.empty():
            self._queue.get_nowait()
        self._queue.put_nowait(None)

    async def stream(self) -> AsyncIterator[HueriseEvent]:
        for event in self._backlog:
            yield event
        while True:
            event = await self._queue.get()
            if event is None:
                return
            yield event


class EventStreamHub:
    """Fans bus events out to every attached client.

    The bus owns ordering and the replay buffer; the hub only tracks who is
    listening and what happens when one of them stalls.
    """

    def __init__(
        self, bus: EventBus, max_pending: int = MAX_PENDING_PER_CLIENT
    ) -> None:
        self._bus = bus
        self._max_pending = max_pending
        self._subscriptions: set[_Subscription] = set()
        self._bus.on(HueriseEvent, self._fan_out)

    @property
    def subscriber_count(self) -> int:
        return len(self._subscriptions)

    def publish(self, event: HueriseEvent) -> None:
        self._bus.dispatch(event)

    @asynccontextmanager
    async def subscribe(
        self, last_event_id: str | None = None
    ) -> AsyncGenerator[AsyncIterator[HueriseEvent]]:
        # Replay and registration must stay in one synchronous block: the bus
        # runs handlers only at an await point, so nothing can slip through the
        # gap between reading history and being listed for fan-out.
        subscription = _Subscription(
            self._replay_after(last_event_id), self._max_pending
        )
        self._subscriptions.add(subscription)
        logger.info("Event stream attached (%d listening)", self.subscriber_count)

        try:
            yield subscription.stream()
        finally:
            self._subscriptions.discard(subscription)
            subscription.close()
            logger.info("Event stream detached (%d listening)", self.subscriber_count)

    def close(self) -> None:
        for subscription in list(self._subscriptions):
            subscription.close()
        self._subscriptions.clear()

    def _fan_out(self, event: HueriseEvent) -> None:
        for subscription in list(self._subscriptions):
            subscription.offer(event)

    def _replay_after(self, last_event_id: str | None) -> list[HueriseEvent]:
        """Events the bus still holds that came after `last_event_id`.

        An id the buffer no longer knows replays nothing: that client was away
        long enough to need a full resync over REST regardless.
        """
        if last_event_id is None:
            return []

        history = [e for e in self._bus.history if isinstance(e, HueriseEvent)]
        for index, event in enumerate(history):
            if event.id == last_event_id:
                return history[index + 1 :]
        return []
