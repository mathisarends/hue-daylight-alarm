from datetime import datetime, timezone
from uuid import UUID, uuid4


class Entity:
    def __init__(
        self, id: UUID | None = None, created_at: datetime | None = None
    ) -> None:
        self.id: UUID = id if id is not None else uuid4()
        self.created_at: datetime = (
            created_at if created_at is not None else datetime.now(timezone.utc)
        )


# semantic sugar: distinguishes aggregate roots from plain entities in signatures
Aggregate = Entity
