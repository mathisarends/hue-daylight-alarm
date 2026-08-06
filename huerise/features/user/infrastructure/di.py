from dishka import Provider, Scope, provide
from sqlalchemy.ext.asyncio import AsyncSession

from huerise.features.user.application import UserService
from huerise.features.user.domain import UserRepository
from huerise.features.user.infrastructure.persistence import SQLUserRepository


class UserProvider(Provider):
    scope = Scope.REQUEST

    @provide
    def user_repository(self, session: AsyncSession) -> UserRepository:
        return SQLUserRepository(session)

    @provide
    def user_service(self, users: UserRepository) -> UserService:
        return UserService(users)
