from sqlalchemy.ext.asyncio import AsyncSession

from huerise.features.user.domain import User, UserRepository
from huerise.infrastructure.database import Repository, UserModel


class SQLUserRepository(Repository[UserModel, User], UserRepository):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, UserModel)

    async def find_by_username(self, username: str) -> User | None:
        return await self.find_by(username=username)

    def _to_domain(self, orm: UserModel) -> User:
        return User(
            id=orm.id,
            username=orm.username,
            password_hash=orm.password_hash,
            created_at=orm.created_at,
        )

    def _to_orm(self, domain: User) -> UserModel:
        return UserModel(
            id=domain.id,
            username=domain.username,
            password_hash=domain.password_hash,
            created_at=domain.created_at,
        )
