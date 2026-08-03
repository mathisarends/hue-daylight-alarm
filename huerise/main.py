from dishka import make_async_container
from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI

from huerise.infrastructure.di import AlarmProvider, DatabaseProvider, SchedulerProvider
from huerise.lifespan import lifespan
from huerise.presentation import router
from huerise.presentation.api.exception_mappings import register_exception_handlers

_container = make_async_container(
    DatabaseProvider(),
    AlarmProvider(),
    SchedulerProvider(),
)

app = FastAPI(
    title="Huerise Alarm API",
    version="1.0.0",
    description="API for managing sunrise alarms with Philips Hue",
    lifespan=lifespan,
)

setup_dishka(_container, app=app)
app.include_router(router)
register_exception_handlers(app)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("huerise.main:app", host="127.0.0.1", port=8000, reload=True)
