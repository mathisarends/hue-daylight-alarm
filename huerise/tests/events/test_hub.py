import pytest

from huerise.tests.events.conftest import make_created, make_hub, take


async def test_publish_reaches_an_attached_client() -> None:
    bus, hub = make_hub()
    event = make_created()

    async with hub.subscribe() as stream:
        hub.publish(event)
        await bus.idle()

        assert await anext(stream) is event


async def test_every_client_receives_the_same_event() -> None:
    bus, hub = make_hub()
    event = make_created()

    async with hub.subscribe() as first, hub.subscribe() as second:
        assert hub.subscriber_count == 2
        hub.publish(event)
        await bus.idle()

        assert await anext(first) is event
        assert await anext(second) is event


async def test_events_arrive_in_publish_order() -> None:
    bus, hub = make_hub()
    published = [make_created() for _ in range(3)]

    async with hub.subscribe() as stream:
        for event in published:
            hub.publish(event)
        await bus.idle()

        assert await take(stream, 3) == published


async def test_detaching_stops_delivery() -> None:
    bus, hub = make_hub()

    async with hub.subscribe():
        pass

    assert hub.subscriber_count == 0
    hub.publish(make_created())
    await bus.idle()


async def test_closing_the_hub_ends_every_stream() -> None:
    _, hub = make_hub()

    async with hub.subscribe() as stream:
        hub.close()

        with pytest.raises(StopAsyncIteration):
            await anext(stream)


async def test_client_that_falls_behind_is_dropped() -> None:
    bus, hub = make_hub(max_pending=2)

    async with hub.subscribe() as stream:
        for _ in range(5):
            hub.publish(make_created())
        await bus.idle()

        with pytest.raises(StopAsyncIteration):
            await anext(stream)


async def test_dropping_one_client_leaves_the_bus_working() -> None:
    bus, hub = make_hub(max_pending=2)

    async with hub.subscribe():
        for _ in range(5):
            hub.publish(make_created())
        await bus.idle()

        async with hub.subscribe() as healthy:
            event = make_created()
            hub.publish(event)
            await bus.idle()

            assert await anext(healthy) is event


async def test_replay_resumes_after_the_last_seen_event() -> None:
    bus, hub = make_hub()
    seen, first_missed, second_missed = (make_created() for _ in range(3))
    for event in (seen, first_missed, second_missed):
        hub.publish(event)
    await bus.idle()

    async with hub.subscribe(last_event_id=seen.id) as stream:
        assert await take(stream, 2) == [first_missed, second_missed]


async def test_replay_is_followed_by_live_events() -> None:
    bus, hub = make_hub()
    seen, missed = make_created(), make_created()
    for event in (seen, missed):
        hub.publish(event)
    await bus.idle()

    async with hub.subscribe(last_event_id=seen.id) as stream:
        live = make_created()
        hub.publish(live)
        await bus.idle()

        assert await take(stream, 2) == [missed, live]


async def test_unknown_last_event_id_replays_nothing() -> None:
    bus, hub = make_hub()
    hub.publish(make_created())
    await bus.idle()

    async with hub.subscribe(last_event_id="rolled-out-of-the-buffer") as stream:
        live = make_created()
        hub.publish(live)
        await bus.idle()

        assert await anext(stream) is live


async def test_without_a_last_event_id_only_live_events_arrive() -> None:
    bus, hub = make_hub()
    hub.publish(make_created())
    await bus.idle()

    async with hub.subscribe() as stream:
        live = make_created()
        hub.publish(live)
        await bus.idle()

        assert await anext(stream) is live
