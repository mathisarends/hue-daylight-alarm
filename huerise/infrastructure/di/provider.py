from collections.abc import AsyncIterator

from dishka import Provider, Scope, provide
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from huerise.application.alarm_service import (
    AlarmRunner,
    AlarmScheduler,
    AlarmService,
    AudioPlayer,
    Lights,
)

from huerise.domain import AlarmRepository
from huerise.infrastructure.adapters.mock_hue import MockHueLights
from huerise.infrastructure.adapters.pyaudio import SoundDeviceAudioPlayer
from huerise.infrastructure.credentials import DatabaseSettings
from huerise.infrastructure.persistence import (
    BackgroundAlarmRepository,
    SQLModelAlarmRepository,
)


class DatabaseProvider(Provider):
    scope = Scope.APP

    @provide
    def get_settings(self) -> DatabaseSettings:
        return DatabaseSettings()

    @provide
    def get_engine(self, settings: DatabaseSettings) -> AsyncEngine:
        return create_async_engine(settings.async_url, echo=False)

    @provide
    def get_session_factory(
        self, engine: AsyncEngine
    ) -> async_sessionmaker[AsyncSession]:
        return async_sessionmaker(engine, expire_on_commit=False)

    @provide(scope=Scope.REQUEST)
    async def get_session(
        self, factory: async_sessionmaker[AsyncSession]
    ) -> AsyncIterator[AsyncSession]:
        async with factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise


class AlarmProvider(Provider):
    scope = Scope.REQUEST

    @provide
    def get_alarm_repository(self, session: AsyncSession) -> AlarmRepository:
        return SQLModelAlarmRepository(session)

    @provide
    def get_alarm_service(
        self, repo: AlarmRepository, audio: AudioPlayer
    ) -> AlarmService:
        return AlarmService(alarm_repository=repo, audio=audio)


class SchedulerProvider(Provider):
    scope = Scope.APP

    @provide
    def get_lights(self) -> Lights:
        return MockHueLights()

    @provide
    def get_audio(self) -> AudioPlayer:
        return SoundDeviceAudioPlayer()

    @provide
    def get_background_repo(
        self, factory: async_sessionmaker[AsyncSession]
    ) -> BackgroundAlarmRepository:
        return BackgroundAlarmRepository(factory)

    @provide
    def get_alarm_runner(
        self,
        lights: Lights,
        audio: AudioPlayer,
        repo: BackgroundAlarmRepository,
    ) -> AlarmRunner:
        return AlarmRunner(lights=lights, audio=audio, repo=repo)

    @provide
    def get_alarm_scheduler(
        self,
        repo: BackgroundAlarmRepository,
        runner: AlarmRunner,
    ) -> AlarmScheduler:
        return AlarmScheduler(repo=repo, runner=runner)
