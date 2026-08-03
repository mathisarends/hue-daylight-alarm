from collections.abc import AsyncIterator

from dishka import Provider, Scope, provide
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from huerise.infrastructure.database import DatabaseSettings


class DatabaseProvider(Provider):
    scope = Scope.APP

    @provide
    def settings(self) -> DatabaseSettings:
        return DatabaseSettings()

    @provide
    def engine(self, settings: DatabaseSettings) -> AsyncEngine:
        return create_async_engine(settings.async_url, echo=False)

    @provide
    def session_factory(self, engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
        return async_sessionmaker(engine, expire_on_commit=False)

    @provide(scope=Scope.REQUEST)
    async def session(
        self, factory: async_sessionmaker[AsyncSession]
    ) -> AsyncIterator[AsyncSession]:
        async with factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
