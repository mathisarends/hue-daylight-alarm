from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from huerise.features.alarm.domain.exceptions import (
    AlarmAlreadyInStateError,
    AlarmNotFoundError,
    AlarmProfileNotFoundError,
    InvalidOccurrenceTransitionError,
    NoActiveOccurrenceError,
    OccurrenceNotFoundError,
    OccurrenceNotRunningError,
)

_HANDLERS: list[tuple[type[Exception], int, str]] = [
    (AlarmNotFoundError, 404, "Alarm not found"),
    (AlarmProfileNotFoundError, 404, "Alarm profile not found"),
    (OccurrenceNotFoundError, 404, "Occurrence not found"),
    (AlarmAlreadyInStateError, 409, "Alarm is already in that state"),
    (NoActiveOccurrenceError, 409, "Alarm has no active occurrence"),
    (OccurrenceNotRunningError, 409, "Occurrence is not currently running"),
    (InvalidOccurrenceTransitionError, 409, "Invalid occurrence transition"),
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
