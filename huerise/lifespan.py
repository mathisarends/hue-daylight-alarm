import asyncio
import contextlib
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from hueify import Hueify
from hueify.models import ResourceType, SceneEvent

from huerise.features.events.application import NextAlarmTracker
from huerise.features.scheduler.application import AlarmScheduler

logger = logging.getLogger(__name__)


async def _log_scene_event(event: SceneEvent) -> None:
    logger.info("Hue scene event: %s", event.model_dump(exclude_none=True))


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler = await app.state.dishka_container.get(AlarmScheduler)

    # Resolving the tracker is what subscribes it to the bus; nothing asks for
    # it later, so without this the derived events would never be emitted.
    tracker = await app.state.dishka_container.get(NextAlarmTracker)
    await tracker.start()

    # Closing the container closes Hueify, which stops the stream with it.
    hue = await app.state.dishka_container.get(Hueify)
    hue.on(ResourceType.SCENE, _log_scene_event)
    await hue.start_events()

    task = asyncio.create_task(scheduler.run())
    try:
        yield
    finally:
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task
        await app.state.dishka_container.close()
