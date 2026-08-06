from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from huerise.features.auth.domain import RefreshToken, RefreshTokenRepository
from huerise.infrastructure.database import RefreshTokenModel, Repository


class SQLRefreshTokenRepository(
    Repository[RefreshTokenModel, RefreshToken], RefreshTokenRepository
):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, RefreshTokenModel)

    async def find_by_token_hash(self, token_hash: str) -> RefreshToken | None:
        return await self.find_by(token_hash=token_hash)

    async def revoke_all_for_user(self, user_id: UUID) -> None:
        stmt = (
            update(RefreshTokenModel)
            .where(
                RefreshTokenModel.user_id == user_id,
                RefreshTokenModel.revoked_at.is_(None),
            )
            .values(revoked_at=datetime.now(UTC))
        )
        await self.session.execute(stmt)

    def _to_domain(self, orm: RefreshTokenModel) -> RefreshToken:
        return RefreshToken(
            id=orm.id,
            user_id=orm.user_id,
            token_hash=orm.token_hash,
            expires_at=orm.expires_at,
            revoked_at=orm.revoked_at,
            created_at=orm.created_at,
        )

    def _to_orm(self, domain: RefreshToken) -> RefreshTokenModel:
        return RefreshTokenModel(
            id=domain.id,
            user_id=domain.user_id,
            token_hash=domain.token_hash,
            created_at=domain.created_at,
            expires_at=domain.expires_at,
            revoked_at=domain.revoked_at,
        )
