import secrets

from dishka.integrations.fastapi import FromDishka, inject
from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

from huerise.env import AppSettings

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


@inject
async def require_api_key(
    settings: FromDishka[AppSettings],
    supplied: str | None = Security(_api_key_header),
) -> None:
    expected = settings.api_key.get_secret_value()
    if supplied is None or not secrets.compare_digest(supplied, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )
