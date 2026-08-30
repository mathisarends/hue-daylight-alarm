import pytest

from huerise.features.user.application import UserService
from huerise.features.user.domain import UsernameAlreadyTakenError
from huerise.features.user.infrastructure.persistence import SQLUserRepository


class TestSQLUserRepository:
    async def test_username_roundtrips(self, session_factory) -> None:
        async with session_factory() as session:
            service = UserService(SQLUserRepository(session))
            registered = await service.register("alice", "correct horse battery staple")
            await session.commit()

        async with session_factory() as session:
            found = await SQLUserRepository(session).find_by_username("alice")

        assert found is not None
        assert found.id == registered.id
        assert found.password_hash != "correct horse battery staple"


class TestUserService:
    async def test_register_rejects_a_taken_username(self, session_factory) -> None:
        async with session_factory() as session:
            service = UserService(SQLUserRepository(session))
            await service.register("bob", "first-password")
            await session.commit()

        async with session_factory() as session:
            service = UserService(SQLUserRepository(session))
            with pytest.raises(UsernameAlreadyTakenError):
                await service.register("bob", "second-password")

    async def test_verify_password_accepts_the_registered_password(
        self, session_factory
    ) -> None:
        async with session_factory() as session:
            service = UserService(SQLUserRepository(session))
            user = await service.register("carol", "s3cret-passphrase")

        assert UserService.verify_password(user, "s3cret-passphrase")

    async def test_verify_password_rejects_a_wrong_password(
        self, session_factory
    ) -> None:
        async with session_factory() as session:
            service = UserService(SQLUserRepository(session))
            user = await service.register("dave", "s3cret-passphrase")

        assert not UserService.verify_password(user, "wrong-passphrase")
