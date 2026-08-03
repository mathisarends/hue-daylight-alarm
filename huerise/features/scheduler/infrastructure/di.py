from dishka import Provider, Scope, provide
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from huerise.features.alarm.infrastructure.persistence import (
    BackgroundAlarmRepository,
)
from huerise.features.runner.application.runner_port import AlarmRunner
from huerise.features.scheduler.application import AlarmScheduler


class SchedulerProvider(Provider):
    scope = Scope.APP

    @provide
    def background_alarm_repository(
        self, factory: async_sessionmaker[AsyncSession]
    ) -> BackgroundAlarmRepository:
        return BackgroundAlarmRepository(factory)

    @provide
    def alarm_scheduler(
        self,
        repo: BackgroundAlarmRepository,
        runner: AlarmRunner,
    ) -> AlarmScheduler:
        return AlarmScheduler(repo=repo, runner=runner)
