from dataclasses import dataclass
from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from huerise.infrastructure.auth import (
    AuthSettings,
    InvalidAccessTokenError,
    decode_access_token,
)

_settings = AuthSettings()

_bearer_scheme = HTTPBearer(
    scheme_name="AccessToken",
    description="Send the /auth/login access token as `Authorization: Bearer <token>`.",
    auto_error=False,
)

_UNAUTHORIZED = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Missing or invalid access token",
    headers={"WWW-Authenticate": "Bearer"},
)


@dataclass(frozen=True, slots=True)
class CurrentUser:
    id: UUID
    tenant_id: UUID


async def get_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None, Depends(_bearer_scheme)
    ],
) -> CurrentUser:
    if credentials is None:
        raise _UNAUTHORIZED
    try:
        user_id, tenant_id = decode_access_token(
            credentials.credentials, _settings.jwt_secret.get_secret_value()
        )
    except InvalidAccessTokenError as error:
        raise _UNAUTHORIZED from error
    return CurrentUser(id=user_id, tenant_id=tenant_id)
