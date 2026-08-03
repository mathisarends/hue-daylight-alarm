import json
import uuid
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from huerise.alarm.domain import Alarm, AlarmRepository
from huerise.alarm.domain.views import (
    AlarmStatus,
    AlarmType,
    IntroConfig,
    RingtoneConfig,
    Schedule,
    SunriseConfig,
    Weekday,
)
from huerise.alarm.infrastructure.persistence.orm import AlarmModel


class SQLModelAlarmRepository(AlarmRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, alarm_id: uuid.UUID) -> Alarm | None:
        model = await self._session.get(AlarmModel, alarm_id)
        return self._to_domain(model) if model is not None else None

    async def get_all(self) -> Sequence[Alarm]:
        result = await self._session.execute(select(AlarmModel))
        return [self._to_domain(m) for m in result.scalars().all()]

    async def get_scheduled(self) -> Sequence[Alarm]:
        result = await self._session.execute(
            select(AlarmModel).where(AlarmModel.status == AlarmStatus.SCHEDULED.value)
        )
        return [self._to_domain(m) for m in result.scalars().all()]

    async def save(self, alarm: Alarm) -> Alarm:
        model = self._to_model(alarm)
        merged = await self._session.merge(model)
        self._session.add(merged)
        await self._session.flush()
        return alarm

    async def delete(self, alarm_id: uuid.UUID) -> None:
        model = await self._session.get(AlarmModel, alarm_id)
        if model is not None:
            await self._session.delete(model)
            await self._session.flush()

    @staticmethod
    def _to_model(alarm: Alarm) -> AlarmModel:
        recurrence_json: str | None = None
        if alarm.schedule.recurrence is not None:
            recurrence_json = json.dumps(
                sorted(int(d) for d in alarm.schedule.recurrence)
            )

        return AlarmModel(
            id=alarm.id,
            label=alarm.label,
            status=alarm.status.value,
            alarm_type=alarm.alarm_type.value,
            series_id=alarm.series_id,
            created_at=alarm.created_at,
            schedule_hour=alarm.schedule.hour,
            schedule_minute=alarm.schedule.minute,
            schedule_recurrence=recurrence_json,
            intro_audio_file=alarm.intro_config.audio_file,
            sunrise_room_name=alarm.sunrise_config.room_name,
            sunrise_scene_name=alarm.sunrise_config.scene_name,
            sunrise_duration_minutes=alarm.sunrise_config.duration_minutes,
            sunrise_brightness_start=alarm.sunrise_config.brightness_start,
            sunrise_brightness_end=alarm.sunrise_config.brightness_end,
            sunrise_steps=alarm.sunrise_config.steps,
            ringtone_audio_file=alarm.ringtone_config.audio_file,
            ringtone_volume=alarm.ringtone_config.volume,
        )

    @staticmethod
    def _to_domain(m: AlarmModel) -> Alarm:
        recurrence: frozenset[Weekday] | None = None
        if m.schedule_recurrence is not None:
            recurrence = frozenset(
                Weekday(d) for d in json.loads(m.schedule_recurrence)
            )

        return Alarm(
            id=m.id,
            label=m.label,
            status=AlarmStatus(m.status),
            alarm_type=AlarmType(m.alarm_type),
            series_id=m.series_id,
            created_at=m.created_at,
            schedule=Schedule(
                hour=m.schedule_hour,
                minute=m.schedule_minute,
                recurrence=recurrence,
            ),
            intro_config=IntroConfig(audio_file=m.intro_audio_file),
            sunrise_config=SunriseConfig(
                room_name=m.sunrise_room_name,
                scene_name=m.sunrise_scene_name,
                duration_minutes=m.sunrise_duration_minutes,
                brightness_start=m.sunrise_brightness_start,
                brightness_end=m.sunrise_brightness_end,
                steps=m.sunrise_steps,
            ),
            ringtone_config=RingtoneConfig(
                audio_file=m.ringtone_audio_file,
                volume=m.ringtone_volume,
            ),
        )


class BackgroundAlarmRepository(AlarmRepository):
    """Session-per-operation repository for use in long-running background tasks."""

    def __init__(self, factory: async_sessionmaker[AsyncSession]) -> None:
        self._factory = factory

    async def get(self, alarm_id: uuid.UUID) -> Alarm | None:
        async with self._factory() as session:
            return await SQLModelAlarmRepository(session).get(alarm_id)

    async def get_all(self) -> Sequence[Alarm]:
        async with self._factory() as session:
            return await SQLModelAlarmRepository(session).get_all()

    async def get_scheduled(self) -> Sequence[Alarm]:
        async with self._factory() as session:
            return await SQLModelAlarmRepository(session).get_scheduled()

    async def save(self, alarm: Alarm) -> Alarm:
        async with self._factory() as session:
            await SQLModelAlarmRepository(session).save(alarm)
            await session.commit()
            return alarm

    async def delete(self, alarm_id: uuid.UUID) -> None:
        async with self._factory() as session:
            await SQLModelAlarmRepository(session).delete(alarm_id)
            await session.commit()
