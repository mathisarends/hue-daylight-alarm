import secrets
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class ApiSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="API_",
        extra="ignore",
    )

    access_token: SecretStr


_settings = ApiSettings()

_bearer_scheme = HTTPBearer(
    scheme_name="AccessToken",
    description="Send the API access token as `Authorization: Bearer <token>`.",
    auto_error=False,
)

_UNAUTHORIZED = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Missing or invalid access token",
    headers={"WWW-Authenticate": "Bearer"},
)


async def require_access_token(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None, Depends(_bearer_scheme)
    ],
) -> None:
    if credentials is None:
        raise _UNAUTHORIZED

    expected = _settings.access_token.get_secret_value()
    if not secrets.compare_digest(credentials.credentials, expected):
        raise _UNAUTHORIZED
