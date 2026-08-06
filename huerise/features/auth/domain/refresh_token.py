from datetime import UTC, datetime
from uuid import UUID

from huerise.shared.ddd import Entity


class RefreshToken(Entity):
    def __init__(
        self,
        user_id: UUID,
        token_hash: str,
        expires_at: datetime,
        revoked_at: datetime | None = None,
        id: UUID | None = None,
        created_at: datetime | None = None,
    ) -> None:
        super().__init__(id, created_at)
        self.user_id = user_id
        self.token_hash = token_hash
        self.expires_at = expires_at
        self.revoked_at = revoked_at

    @property
    def is_active(self) -> bool:
        return self.revoked_at is None

    def revoke(self) -> None:
        if self.revoked_at is None:
            self.revoked_at = datetime.now(UTC)
