import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI

from huerise.application import AlarmScheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler = await app.state.dishka_container.get(AlarmScheduler)

    task = asyncio.create_task(scheduler.run())
    try:
        yield
    finally:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
        await app.state.dishka_container.close()
