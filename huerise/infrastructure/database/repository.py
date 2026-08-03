from abc import ABC, abstractmethod
from typing import Any
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from huerise.infrastructure.database.models import DatabaseEntity


class Repository[ORM: DatabaseEntity, Domain](ABC):
    """Generic persistence for one aggregate: querying here, mapping in subclasses."""

    def __init__(self, session: AsyncSession, model: type[ORM]) -> None:
        self.session = session
        self.model = model

    @abstractmethod
    def _to_domain(self, orm: ORM) -> Domain: ...

    @abstractmethod
    def _to_orm(self, domain: Domain) -> ORM: ...

    async def find_by_id(self, id: UUID) -> Domain | None:
        orm = await self.session.get(self.model, id)
        return self._to_domain(orm) if orm is not None else None

    async def find_by(self, **filters: Any) -> Domain | None:
        stmt = select(self.model).filter_by(**filters)
        orm = await self.session.scalar(stmt)
        return self._to_domain(orm) if orm is not None else None

    async def find_all(
        self, *, limit: int | None = None, offset: int | None = None, **filters: Any
    ) -> list[Domain]:
        stmt = select(self.model).filter_by(**filters)
        if offset is not None:
            stmt = stmt.offset(offset)
        if limit is not None:
            stmt = stmt.limit(limit)
        result = await self.session.scalars(stmt)
        return [self._to_domain(orm) for orm in result.all()]

    async def save(self, domain: Domain) -> Domain:
        merged = await self.session.merge(self._to_orm(domain))
        await self.session.flush()
        await self.session.refresh(merged)
        return self._to_domain(merged)

    async def delete_by_id(self, id: UUID) -> bool:
        stmt = delete(self.model).where(self.model.id == id)
        result = await self.session.execute(stmt)
        return result.rowcount > 0

    async def exists(self, **filters: Any) -> bool:
        stmt = select(self.model.id).filter_by(**filters).limit(1)
        return await self.session.scalar(stmt) is not None
