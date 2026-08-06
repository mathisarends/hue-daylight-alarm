from abc import ABC, abstractmethod
from uuid import UUID

from huerise.features.user.domain.user import User


class UserRepository(ABC):
    @abstractmethod
    async def find_by_id(self, id: UUID) -> User | None: ...

    @abstractmethod
    async def find_by_username(self, username: str) -> User | None: ...

    @abstractmethod
    async def save(self, domain: User) -> User: ...
