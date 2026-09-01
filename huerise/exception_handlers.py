from collections.abc import Callable, Mapping
from dataclasses import dataclass
from functools import wraps
from typing import Any

from fastapi import APIRouter, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from huerise.configuration import ConfigurationError, ConfigurationIssue


class ErrorResponse(BaseModel):
    detail: str


class ConfigurationErrorResponse(ErrorResponse):
    issues: list[ConfigurationIssue]


@dataclass(frozen=True, slots=True)
class Error:
    status_code: int
    description: str


type Errors = Mapping[type[Exception], Error]
type Endpoint = Callable[..., Any]
type RouteDecorator = Callable[[Endpoint], Endpoint]


def error(status_code: int, description: str) -> Error:
    return Error(status_code, description)


async def request_validation_error(
    _: Request, exception: RequestValidationError
) -> JSONResponse:
    issues = [
        {
            "location": ".".join(str(part) for part in issue["loc"]),
            "message": issue["msg"],
            "type": issue["type"],
        }
        for issue in exception.errors()
    ]
    return JSONResponse(
        status_code=422,
        content={"detail": "Request validation failed", "issues": issues},
    )


class ExceptionRouter(APIRouter):
    def get(
        self, path: str, *, errors: Errors | None = None, **kwargs: Any
    ) -> RouteDecorator:
        return self._route(super().get, path, errors, kwargs)

    def post(
        self, path: str, *, errors: Errors | None = None, **kwargs: Any
    ) -> RouteDecorator:
        return self._route(super().post, path, errors, kwargs)

    def put(
        self, path: str, *, errors: Errors | None = None, **kwargs: Any
    ) -> RouteDecorator:
        return self._route(super().put, path, errors, kwargs)

    @staticmethod
    def _route(
        route: Callable[..., RouteDecorator],
        path: str,
        errors: Errors | None,
        kwargs: dict[str, Any],
    ) -> RouteDecorator:
        if not errors:
            return route(path, **kwargs)

        kwargs["responses"] = _responses(errors, kwargs.get("responses"))
        register = route(path, **kwargs)

        def decorator(endpoint: Endpoint) -> Endpoint:
            @wraps(endpoint)
            async def handled(*args: Any, **endpoint_kwargs: Any) -> Any:
                try:
                    return await endpoint(*args, **endpoint_kwargs)
                except tuple(errors) as exception:
                    mapping = next(
                        value
                        for exception_type, value in errors.items()
                        if isinstance(exception, exception_type)
                    )
                    return JSONResponse(
                        status_code=mapping.status_code,
                        content=_content(exception),
                    )

            return register(handled)

        return decorator


def _responses(
    errors: Errors, responses: dict[int | str, dict[str, Any]] | None
) -> dict[int | str, dict[str, Any]]:
    documented = dict(responses or {})
    for exception_type, mapping in errors.items():
        response = documented.setdefault(
            mapping.status_code,
            {
                "description": mapping.description,
                "model": _response_model(exception_type),
            },
        )
        if mapping.description not in response["description"]:
            response["description"] += f"\n\n{mapping.description}"
    return documented


def _response_model(exception_type: type[Exception]) -> Any:
    if issubclass(exception_type, ConfigurationError):
        return ConfigurationErrorResponse
    return ErrorResponse


def _content(exception: Exception) -> dict[str, Any]:
    content: dict[str, Any] = {"detail": str(exception)}
    if isinstance(exception, ConfigurationError):
        content["issues"] = [issue.model_dump() for issue in exception.issues]
    return content
