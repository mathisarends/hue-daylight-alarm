from datetime import datetime
from uuid import UUID

from huerise.shared.ddd import Entity


class User(Entity):
    def __init__(
        self,
        username: str,
        password_hash: str,
        id: UUID | None = None,
        created_at: datetime | None = None,
    ) -> None:
        super().__init__(id, created_at)
        self.username = username
        self.password_hash = password_hash
