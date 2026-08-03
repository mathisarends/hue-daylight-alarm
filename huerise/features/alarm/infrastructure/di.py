from dishka import Provider, Scope, provide
from sqlalchemy.ext.asyncio import AsyncSession

from huerise.features.alarm.application import AlarmService, AudioPlayer
from huerise.features.alarm.domain import AlarmRepository
from huerise.features.alarm.infrastructure.persistence import SQLModelAlarmRepository


class AlarmProvider(Provider):
    scope = Scope.REQUEST

    @provide
    def alarm_repository(self, session: AsyncSession) -> AlarmRepository:
        return SQLModelAlarmRepository(session)

    @provide
    def alarm_service(self, repo: AlarmRepository, audio: AudioPlayer) -> AlarmService:
        return AlarmService(alarm_repository=repo, audio=audio)
