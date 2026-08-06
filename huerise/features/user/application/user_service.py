from argon2 import PasswordHasher
from argon2.exceptions import VerificationError

from huerise.features.user.domain import (
    User,
    UsernameAlreadyTakenError,
    UserRepository,
)

_hasher = PasswordHasher()
# Verified on every login for an unknown username, so response timing can't
# reveal whether the username exists.
_DUMMY_HASH = _hasher.hash("huerise-dummy-password-for-timing-safety")


def _verify(password_hash: str, password: str) -> bool:
    try:
        return _hasher.verify(password_hash, password)
    except VerificationError:
        return False


class UserService:
    def __init__(self, users: UserRepository) -> None:
        self._users = users

    async def register(self, username: str, password: str) -> User:
        if await self._users.find_by_username(username) is not None:
            raise UsernameAlreadyTakenError(username)
        user = User(username=username, password_hash=_hasher.hash(password))
        return await self._users.save(user)

    async def find_by_username(self, username: str) -> User | None:
        return await self._users.find_by_username(username)

    @staticmethod
    def verify_password(user: User, password: str) -> bool:
        return _verify(user.password_hash, password)

    async def authenticate(self, username: str, password: str) -> User | None:
        user = await self._users.find_by_username(username)
        password_hash = user.password_hash if user is not None else _DUMMY_HASH
        return user if _verify(password_hash, password) else None
