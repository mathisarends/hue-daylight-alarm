from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from dishka import AsyncContainer, make_async_container
from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from huerise.configuration import ConfigurationError
from huerise.features import FEATURES
from huerise.features.daylight_alarm.service import (
    AlarmAlreadyRunningError,
    DaylightAlarm,
)
from huerise.features.lighting.hue import (
    HueUnavailableError,
    RoomNotFoundError,
    SceneNotFoundError,
)
from huerise.features.lighting.onboarding import (
    BridgeNotFoundError,
    BridgeNotSelectedError,
    LinkButtonTimeoutError,
    OnboardingReadOnlyError,
)
from huerise.providers import CoreProvider


class HealthResponse(BaseModel):
    status: str


def create_container() -> AsyncContainer:
    providers = [
        CoreProvider(),
        *(provider() for feature in FEATURES for provider in feature.providers),
    ]
    return make_async_container(*providers)


def create_app(container: AsyncContainer | None = None) -> FastAPI:
    container = container or create_container()

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        try:
            yield
        finally:
            alarm = await container.get(DaylightAlarm)
            await alarm.stop()
            await container.close()

    app = FastAPI(
        title="Huerise Daylight Alarm API",
        version="2.0.0",
        description="Run one YAML-configured Philips Hue daylight alarm.",
        lifespan=lifespan,
    )
    setup_dishka(container, app=app)
    _install_exception_handlers(app)

    @app.get("/health", response_model=HealthResponse, tags=["health"])
    async def health() -> HealthResponse:
        return HealthResponse(status="ok")

    for feature in FEATURES:
        feature.install(app)
    return app


def _install_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(ConfigurationError)
    async def configuration_error(
        _: Request, error: ConfigurationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={
                "detail": str(error),
                "issues": [issue.model_dump() for issue in error.issues],
            },
        )

    _map_error(app, AlarmAlreadyRunningError, status.HTTP_409_CONFLICT)
    _map_error(app, OnboardingReadOnlyError, status.HTTP_409_CONFLICT)
    _map_error(app, BridgeNotSelectedError, status.HTTP_409_CONFLICT)
    _map_error(app, LinkButtonTimeoutError, status.HTTP_409_CONFLICT)
    _map_error(app, BridgeNotFoundError, status.HTTP_404_NOT_FOUND)
    _map_error(app, RoomNotFoundError, status.HTTP_404_NOT_FOUND)
    _map_error(app, SceneNotFoundError, status.HTTP_404_NOT_FOUND)
    _map_error(app, HueUnavailableError, status.HTTP_503_SERVICE_UNAVAILABLE)


def _map_error(app: FastAPI, error_type: type[Exception], status_code: int) -> None:
    async def handler(_: Request, error: Exception) -> JSONResponse:
        return JSONResponse(status_code=status_code, content={"detail": str(error)})

    app.add_exception_handler(error_type, handler)
