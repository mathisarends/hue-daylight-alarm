import pytest
from pydantic import SecretStr

from huerise.features.auth.application import AuthService
from huerise.features.auth.domain import (
    InvalidCredentialsError,
    InvalidRefreshTokenError,
)
from huerise.features.auth.infrastructure.persistence import SQLRefreshTokenRepository
from huerise.features.user.application import UserService
from huerise.features.user.infrastructure.persistence import SQLUserRepository
from huerise.infrastructure.auth import AuthSettings


def make_settings() -> AuthSettings:
    return AuthSettings(
        jwt_secret=SecretStr("test-jwt-secret"),
        access_token_ttl_minutes=15,
        refresh_token_ttl_days=30,
    )


def make_service(session) -> AuthService:
    return AuthService(
        UserService(SQLUserRepository(session)),
        SQLRefreshTokenRepository(session),
        make_settings(),
    )


class TestRegisterAndLogin:
    async def test_register_issues_a_usable_token_pair(self, session_factory) -> None:
        async with session_factory() as session:
            service = make_service(session)
            pair = await service.register("alice", "correct-horse-battery")
            await session.commit()

        assert pair.access_token
        assert pair.refresh_token
        assert pair.token_type == "bearer"
        assert pair.expires_in == 15 * 60

    async def test_login_accepts_the_registered_password(self, session_factory) -> None:
        async with session_factory() as session:
            await make_service(session).register("bob", "s3cret-passphrase")
            await session.commit()

        async with session_factory() as session:
            pair = await make_service(session).login("bob", "s3cret-passphrase")

        assert pair.access_token

    async def test_login_rejects_a_wrong_password(self, session_factory) -> None:
        async with session_factory() as session:
            await make_service(session).register("carol", "s3cret-passphrase")
            await session.commit()

        async with session_factory() as session:
            with pytest.raises(InvalidCredentialsError):
                await make_service(session).login("carol", "wrong-password")

    async def test_login_rejects_an_unknown_username(self, session_factory) -> None:
        async with session_factory() as session:
            with pytest.raises(InvalidCredentialsError):
                await make_service(session).login("nobody", "whatever")


class TestRefresh:
    async def test_refresh_rotates_the_token_and_keeps_it_usable(
        self, session_factory
    ) -> None:
        async with session_factory() as session:
            issued = await make_service(session).register("dave", "s3cret-passphrase")
            await session.commit()

        async with session_factory() as session:
            rotated = await make_service(session).refresh(issued.refresh_token)
            await session.commit()

        assert rotated.refresh_token != issued.refresh_token

    async def test_refresh_rejects_an_already_used_token(self, session_factory) -> None:
        async with session_factory() as session:
            issued = await make_service(session).register("erin", "s3cret-passphrase")
            await session.commit()

        async with session_factory() as session:
            await make_service(session).refresh(issued.refresh_token)
            await session.commit()

        async with session_factory() as session:
            with pytest.raises(InvalidRefreshTokenError):
                await make_service(session).refresh(issued.refresh_token)

    async def test_reuse_of_a_rotated_token_burns_the_whole_session(
        self, session_factory
    ) -> None:
        """Presenting an already-rotated token means it leaked -- every active
        token for that user must stop working, including the newest one."""
        async with session_factory() as session:
            issued = await make_service(session).register("frank", "s3cret-passphrase")
            await session.commit()

        async with session_factory() as session:
            rotated = await make_service(session).refresh(issued.refresh_token)
            await session.commit()

        async with session_factory() as session:
            with pytest.raises(InvalidRefreshTokenError):
                await make_service(session).refresh(issued.refresh_token)
            await session.commit()

        async with session_factory() as session:
            with pytest.raises(InvalidRefreshTokenError):
                await make_service(session).refresh(rotated.refresh_token)

    async def test_refresh_rejects_an_unknown_token(self, session_factory) -> None:
        async with session_factory() as session:
            with pytest.raises(InvalidRefreshTokenError):
                await make_service(session).refresh("not-a-real-token")


class TestLogout:
    async def test_logout_revokes_the_refresh_token(self, session_factory) -> None:
        async with session_factory() as session:
            issued = await make_service(session).register("grace", "s3cret-passphrase")
            await session.commit()

        async with session_factory() as session:
            await make_service(session).logout(issued.refresh_token)
            await session.commit()

        async with session_factory() as session:
            with pytest.raises(InvalidRefreshTokenError):
                await make_service(session).refresh(issued.refresh_token)

    async def test_logout_is_idempotent_for_an_unknown_token(
        self, session_factory
    ) -> None:
        async with session_factory() as session:
            await make_service(session).logout("not-a-real-token")
