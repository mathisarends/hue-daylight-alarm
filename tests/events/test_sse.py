import json

import pytest

from huerise.features.events.presentation.sse import (
    KEEPALIVE_FRAME,
    format_frame,
    frames,
)
from tests.events.conftest import make_created, make_hub


def test_frame_carries_id_type_and_payload() -> None:
    event = make_created()

    frame = format_frame(event)

    head, _, data = frame.partition("data: ")
    assert head == f"id: {event.id}\nevent: alarm.created\n"
    assert json.loads(data)["type"] == "alarm.created"
    assert frame.endswith("\n\n")


async def test_events_are_framed_in_order() -> None:
    bus, hub = make_hub()
    published = [make_created() for _ in range(2)]

    async with hub.subscribe() as events:
        stream = frames(events)
        for event in published:
            hub.publish(event)
        await bus.idle()

        assert [await anext(stream) for _ in published] == [
            format_frame(event) for event in published
        ]


async def test_keepalive_arrives_while_the_stream_is_idle() -> None:
    _, hub = make_hub()

    async with hub.subscribe() as events:
        stream = frames(events, keepalive=0.01)

        assert await anext(stream) == KEEPALIVE_FRAME


async def test_keepalive_does_not_end_the_stream() -> None:
    bus, hub = make_hub()

    async with hub.subscribe() as events:
        stream = frames(events, keepalive=0.01)
        assert await anext(stream) == KEEPALIVE_FRAME

        event = make_created()
        hub.publish(event)
        await bus.idle()

        assert await anext(stream) == format_frame(event)


async def test_frames_end_when_the_client_is_dropped() -> None:
    _, hub = make_hub()

    async with hub.subscribe() as events:
        stream = frames(events, keepalive=5)
        hub.close()

        with pytest.raises(StopAsyncIteration):
            await anext(stream)
