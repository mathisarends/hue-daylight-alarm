import asyncio
import contextlib
from contextlib import asynccontextmanager

from fastapi import FastAPI

from huerise.features.scheduler.application import AlarmScheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler = await app.state.dishka_container.get(AlarmScheduler)

    task = asyncio.create_task(scheduler.run())
    try:
        yield
    finally:
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task
        await app.state.dishka_container.close()
