from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from huerise.features.alarm.domain.exceptions import (
    AlarmAlreadyCancelledError,
    AlarmAlreadyInStatusError,
    AlarmNotFoundError,
    AlarmNotRunningError,
)

_HANDLERS: list[tuple[type[Exception], int, str]] = [
    (AlarmNotFoundError, 404, "Alarm not found"),
    (AlarmAlreadyCancelledError, 409, "Alarm is already cancelled"),
    (AlarmAlreadyInStatusError, 409, "Alarm status conflict"),
    (AlarmNotRunningError, 409, "Alarm is not currently running"),
    (ValueError, 400, "Invalid operation"),
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
