import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from dishka import AsyncContainer, make_async_container
from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError

from huerise import __version__
from huerise.env import AppSettings
from huerise.exception_handlers import request_validation_error
from huerise.features import FEATURES
from huerise.features.daylight_alarm.application import DaylightAlarm
from huerise.shared import CoreProvider


def create_container() -> AsyncContainer:
    return make_async_container(
        CoreProvider(),
        *(provider() for feature in FEATURES for provider in feature.providers),
    )


def create_app(container: AsyncContainer | None = None) -> FastAPI:
    container = container or create_container()

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncGenerator[None]:
        settings = await container.get(AppSettings)
        logging.basicConfig(
            level=settings.log_level.value,
            format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        )
        try:
            yield
        finally:
            alarm = await container.get(DaylightAlarm)
            await alarm.stop()
            await container.close()

    app = FastAPI(
        title="Huerise Daylight Alarm API",
        version=__version__,
        description="Run one YAML-configured Philips Hue daylight alarm.",
        lifespan=lifespan,
    )
    app.add_exception_handler(RequestValidationError, request_validation_error)
    setup_dishka(container, app=app)
    for feature in FEATURES:
        feature.install(app)
    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "huerise.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        loop="asyncio",
    )
