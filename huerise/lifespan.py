import asyncio
import contextlib
from contextlib import asynccontextmanager

from fastapi import FastAPI

from huerise.features.devices.application import LightChangeLogger, LightEvents
from huerise.features.events.application import NextAlarmTracker
from huerise.features.scheduler.application import AlarmScheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler = await app.state.dishka_container.get(AlarmScheduler)

    # Resolving the tracker is what subscribes it to the bus; nothing asks for
    # it later, so without this the derived events would never be emitted.
    tracker = await app.state.dishka_container.get(NextAlarmTracker)
    await tracker.start()

    # Same here: resolving the logger is what subscribes it. Closing the
    # container closes Hueify, which stops the event stream with it.
    await app.state.dishka_container.get(LightChangeLogger)
    await (await app.state.dishka_container.get(LightEvents)).start()

    task = asyncio.create_task(scheduler.run())
    try:
        yield
    finally:
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task
        await app.state.dishka_container.close()
