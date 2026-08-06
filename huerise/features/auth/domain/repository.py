from abc import ABC, abstractmethod
from uuid import UUID

from huerise.features.auth.domain.refresh_token import RefreshToken


class RefreshTokenRepository(ABC):
    @abstractmethod
    async def find_by_token_hash(self, token_hash: str) -> RefreshToken | None: ...

    @abstractmethod
    async def save(self, domain: RefreshToken) -> RefreshToken: ...

    @abstractmethod
    async def revoke_all_for_user(self, user_id: UUID) -> None:
        """Stolen-token containment: invalidate every active token at once."""
