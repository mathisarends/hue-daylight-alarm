from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from huerise.features.devices.domain import (
    RoomNotFoundError,
    SceneNotFoundError,
    SoundNotFoundError,
)

_HANDLERS: list[tuple[type[Exception], int, str]] = [
    (SoundNotFoundError, 404, "Sound not found"),
    (RoomNotFoundError, 404, "Room not found"),
    (SceneNotFoundError, 404, "Scene not found"),
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
