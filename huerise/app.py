from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

from fastapi import Depends, FastAPI, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from huerise.authentication import require_api_key
from huerise.configuration import (
    APISettings,
    ConfigurationError,
    HueEnvironment,
    YamlConfiguration,
)
from huerise.daylight_alarm import AlarmAlreadyRunningError, DaylightAlarm
from huerise.hue import (
    HueClientFactory,
    HueCredentialsProvider,
    HueifyClientFactory,
    HueUnavailableError,
    SceneNotFoundError,
)


@dataclass(slots=True)
class AppServices:
    api_key: str
    alarm: DaylightAlarm


class StatusResponse(BaseModel):
    status: str


def build_services(
    settings: APISettings | None = None,
    hue_environment: HueEnvironment | None = None,
    clients: HueClientFactory | None = None,
) -> AppServices:
    settings = settings or APISettings()
    configuration = YamlConfiguration(settings.config_path)
    credentials = HueCredentialsProvider(
        configuration, hue_environment or HueEnvironment()
    )
    alarm = DaylightAlarm(
        configuration,
        credentials,
        clients or HueifyClientFactory(),
    )
    return AppServices(settings.api_key.get_secret_value(), alarm)


def create_app(services: AppServices | None = None) -> FastAPI:
    services = services or build_services()

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        try:
            yield
        finally:
            await services.alarm.stop()

    app = FastAPI(
        title="Huerise Daylight Alarm API",
        version="2.0.0",
        description="Run one YAML-configured Philips Hue daylight alarm.",
        lifespan=lifespan,
    )
    app.state.services = services
    _install_exception_handlers(app)

    @app.get("/health", response_model=StatusResponse, tags=["health"])
    async def health() -> StatusResponse:
        return StatusResponse(status="ok")

    @app.post(
        "/daylight-alarm/start",
        status_code=status.HTTP_202_ACCEPTED,
        response_model=StatusResponse,
        dependencies=[Depends(require_api_key)],
        tags=["daylight-alarm"],
    )
    async def start_daylight_alarm() -> StatusResponse:
        await services.alarm.start()
        return StatusResponse(status="started")

    @app.post(
        "/daylight-alarm/stop",
        status_code=status.HTTP_204_NO_CONTENT,
        response_model=None,
        dependencies=[Depends(require_api_key)],
        tags=["daylight-alarm"],
    )
    async def stop_daylight_alarm() -> None:
        await services.alarm.stop()

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

    @app.exception_handler(AlarmAlreadyRunningError)
    async def alarm_already_running(
        _: Request, error: AlarmAlreadyRunningError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"detail": str(error)},
        )

    @app.exception_handler(SceneNotFoundError)
    async def scene_not_found(_: Request, error: SceneNotFoundError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": str(error)},
        )

    @app.exception_handler(HueUnavailableError)
    async def hue_unavailable(_: Request, error: HueUnavailableError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"detail": str(error)},
        )
