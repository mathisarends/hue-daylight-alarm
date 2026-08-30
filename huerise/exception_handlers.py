from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from huerise.configuration import ConfigurationError
from huerise.features.daylight_alarm.application import AlarmAlreadyRunningError
from huerise.features.lighting.application import (
    BridgeNotFoundError,
    BridgeNotSelectedError,
    HueUnavailableError,
    LinkButtonTimeoutError,
    OnboardingReadOnlyError,
    SceneNotFoundError,
)


def install_exception_handlers(app: FastAPI) -> None:
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
    _map_error(app, SceneNotFoundError, status.HTTP_404_NOT_FOUND)
    _map_error(app, HueUnavailableError, status.HTTP_503_SERVICE_UNAVAILABLE)


def _map_error(app: FastAPI, error_type: type[Exception], status_code: int) -> None:
    async def handler(_: Request, error: Exception) -> JSONResponse:
        return JSONResponse(status_code=status_code, content={"detail": str(error)})

    app.add_exception_handler(error_type, handler)
