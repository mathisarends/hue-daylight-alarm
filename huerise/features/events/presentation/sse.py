import asyncio
from collections.abc import AsyncIterator

from huerise.features.events.domain import HueriseEvent

KEEPALIVE_INTERVAL = 15.0
KEEPALIVE_FRAME = ": keepalive\n\n"


def format_frame(event: HueriseEvent) -> str:
    return f"id: {event.id}\nevent: {event.type}\ndata: {event.model_dump_json()}\n\n"


async def frames(
    events: AsyncIterator[HueriseEvent], keepalive: float = KEEPALIVE_INTERVAL
) -> AsyncIterator[str]:
    """SSE frames, with a comment whenever the stream falls quiet.

    The pending `anext` is carried across timeouts as a task rather than being
    cancelled: cancelling it would close the underlying generator and end the
    stream for good instead of just idling.
    """
    pending = asyncio.ensure_future(anext(events))
    try:
        while True:
            done, _ = await asyncio.wait({pending}, timeout=keepalive)
            if not done:
                yield KEEPALIVE_FRAME
                continue

            try:
                event = pending.result()
            except StopAsyncIteration:
                return

            pending = asyncio.ensure_future(anext(events))
            yield format_frame(event)
    finally:
        pending.cancel()
