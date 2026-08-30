from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from huerise.features.lighting.domain import (
    HueBridgeNotFoundError,
    HueBridgeNotSelectedError,
    HueDiscoveryError,
    HueEnvironmentOverrideError,
    HueLinkButtonTimeoutError,
    HueRegistrationError,
    HueUnavailableError,
    RoomNotFoundError,
    SceneNotFoundError,
)

_HANDLERS: list[tuple[type[Exception], int, str]] = [
    (RoomNotFoundError, 404, "Room not found"),
    (SceneNotFoundError, 404, "Scene not found"),
    (HueBridgeNotFoundError, 404, "Hue Bridge not found"),
    (HueBridgeNotSelectedError, 409, "Hue Bridge not selected"),
    (HueEnvironmentOverrideError, 409, "Hue is environment-controlled"),
    (HueDiscoveryError, 503, "Hue discovery unavailable"),
    (HueLinkButtonTimeoutError, 408, "Hue link button timeout"),
    (HueRegistrationError, 502, "Hue registration failed"),
    (HueUnavailableError, 503, "Hue unavailable"),
]


def _make_handler(status_code: int, default_detail: str):
    async def handler(request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=status_code,
            content={"detail": str(exc) or default_detail},
        )

    return handler


def register_exception_handlers(app: FastAPI) -> None:
    for exc_class, status_code, detail in _HANDLERS:
        app.add_exception_handler(exc_class, _make_handler(status_code, detail))
