from collections.abc import AsyncGenerator
from contextlib import AsyncExitStack, asynccontextmanager

from dishka import Provider, Scope, provide
from fastapi import FastAPI

from huerise.features.alarm.application import LightReferenceSync
from huerise.features.events.application import NextAlarmTracker
from huerise.features.lighting.application import LightEvents
from huerise.features.scheduler.application import AlarmScheduler
from huerise.lifecycle import Runnable


class LifecycleProvider(Provider):
    scope = Scope.APP

    @provide
    def runnables(
        self,
        light_events: LightEvents,
        light_references: LightReferenceSync,
        tracker: NextAlarmTracker,
        scheduler: AlarmScheduler,
    ) -> list[Runnable]:
        return [light_events, light_references, tracker, scheduler]


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    container = app.state.dishka_container
    async with AsyncExitStack() as stack:
        stack.push_async_callback(container.close)
        for runnable in await container.get(list[Runnable]):
            await runnable.start()
            stack.push_async_callback(runnable.stop)
        yield
