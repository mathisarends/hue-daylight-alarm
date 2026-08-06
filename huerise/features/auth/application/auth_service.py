import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID

from huerise.features.auth.domain import (
    InvalidCredentialsError,
    InvalidRefreshTokenError,
    RefreshToken,
    RefreshTokenRepository,
    TokenPair,
)
from huerise.features.user.application import UserService
from huerise.infrastructure.auth import AuthSettings, encode_access_token


def _hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


class AuthService:
    def __init__(
        self,
        users: UserService,
        tokens: RefreshTokenRepository,
        settings: AuthSettings,
    ) -> None:
        self._users = users
        self._tokens = tokens
        self._settings = settings

    async def register(self, username: str, password: str) -> TokenPair:
        user = await self._users.register(username, password)
        return await self._issue_pair(user.id)

    async def login(self, username: str, password: str) -> TokenPair:
        user = await self._users.authenticate(username, password)
        if user is None:
            raise InvalidCredentialsError
        return await self._issue_pair(user.id)

    async def refresh(self, refresh_token: str) -> TokenPair:
        stored = await self._tokens.find_by_token_hash(_hash_token(refresh_token))
        if stored is None or stored.expires_at <= datetime.now(UTC):
            raise InvalidRefreshTokenError

        if not stored.is_active:
            # A revoked token being presented again means it leaked: burn every
            # active token for this user rather than trusting this one request.
            await self._tokens.revoke_all_for_user(stored.user_id)
            raise InvalidRefreshTokenError

        stored.revoke()
        await self._tokens.save(stored)
        return await self._issue_pair(stored.user_id)

    async def logout(self, refresh_token: str) -> None:
        stored = await self._tokens.find_by_token_hash(_hash_token(refresh_token))
        if stored is not None and stored.is_active:
            stored.revoke()
            await self._tokens.save(stored)

    async def _issue_pair(self, user_id: UUID) -> TokenPair:
        # v1 tenant model: a user's own id doubles as their tenant id.
        access_token = encode_access_token(
            user_id=user_id,
            tenant_id=user_id,
            secret=self._settings.jwt_secret.get_secret_value(),
            ttl_minutes=self._settings.access_token_ttl_minutes,
        )
        raw_refresh_token = secrets.token_urlsafe(32)
        expires_at = datetime.now(UTC) + timedelta(
            days=self._settings.refresh_token_ttl_days
        )
        await self._tokens.save(
            RefreshToken(
                user_id=user_id,
                token_hash=_hash_token(raw_refresh_token),
                expires_at=expires_at,
            )
        )
        return TokenPair(
            access_token=access_token,
            refresh_token=raw_refresh_token,
            expires_in=self._settings.access_token_ttl_minutes * 60,
        )
