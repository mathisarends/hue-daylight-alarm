from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt as pyjwt

from huerise.infrastructure.auth.exceptions import InvalidAccessTokenError

_ALGORITHM = "HS256"


def encode_access_token(
    user_id: UUID, tenant_id: UUID, secret: str, ttl_minutes: int
) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "tenant_id": str(tenant_id),
        "iat": now,
        "exp": now + timedelta(minutes=ttl_minutes),
    }
    return pyjwt.encode(payload, secret, algorithm=_ALGORITHM)


def decode_access_token(token: str, secret: str) -> tuple[UUID, UUID]:
    try:
        payload = pyjwt.decode(token, secret, algorithms=[_ALGORITHM])
    except pyjwt.PyJWTError as error:
        raise InvalidAccessTokenError from error
    return UUID(payload["sub"]), UUID(payload["tenant_id"])
