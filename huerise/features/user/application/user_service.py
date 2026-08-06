from argon2 import PasswordHasher
from argon2.exceptions import VerificationError

from huerise.features.user.domain import (
    User,
    UsernameAlreadyTakenError,
    UserRepository,
)

_hasher = PasswordHasher()


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
        try:
            return _hasher.verify(user.password_hash, password)
        except VerificationError:
            return False
