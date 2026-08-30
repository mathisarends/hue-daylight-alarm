from dishka import Provider, Scope, provide
from sqlalchemy.ext.asyncio import AsyncSession

from huerise.features.auth.application import AuthService
from huerise.features.auth.domain import RefreshTokenRepository
from huerise.features.auth.infrastructure.persistence import SQLRefreshTokenRepository
from huerise.features.user.application import UserService
from huerise.infrastructure.auth import AuthSettings


class AuthProvider(Provider):
    scope = Scope.REQUEST

    @provide(scope=Scope.APP)
    def settings(self) -> AuthSettings:
        return AuthSettings()

    @provide
    def refresh_token_repository(self, session: AsyncSession) -> RefreshTokenRepository:
        return SQLRefreshTokenRepository(session)

    @provide
    def auth_service(
        self,
        users: UserService,
        tokens: RefreshTokenRepository,
        settings: AuthSettings,
    ) -> AuthService:
        return AuthService(users, tokens, settings)
