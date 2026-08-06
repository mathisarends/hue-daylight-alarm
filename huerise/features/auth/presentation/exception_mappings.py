from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from huerise.features.auth.domain import (
    InvalidCredentialsError,
    InvalidRefreshTokenError,
)
from huerise.features.user.domain import UsernameAlreadyTakenError

_HANDLERS: list[tuple[type[Exception], int, str]] = [
    (InvalidCredentialsError, 401, "Invalid username or password"),
    (InvalidRefreshTokenError, 401, "Invalid or expired refresh token"),
    (UsernameAlreadyTakenError, 409, "Username is already taken"),
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
