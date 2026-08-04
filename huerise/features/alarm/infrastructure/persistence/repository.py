from datetime import datetime, timedelta
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from huerise.features.alarm.domain import (
    Alarm,
    AlarmOccurrence,
    AlarmOccurrenceRepository,
    AlarmProfile,
    AlarmProfileRepository,
    AlarmRepository,
    IntroConfig,
    OccurrenceState,
    RingtoneConfig,
    Schedule,
    SunriseConfig,
)
from huerise.infrastructure.database import (
    AlarmModel,
    AlarmOccurrenceModel,
    AlarmProfileModel,
    Repository,
)

_WAITING_STATES = (OccurrenceState.PENDING, OccurrenceState.SNOOZED)
_ACTIVE_STATES = (
    OccurrenceState.PENDING,
    OccurrenceState.SNOOZED,
    OccurrenceState.SUNRISE,
    OccurrenceState.RINGING,
)


class SQLAlarmProfileRepository(
    Repository[AlarmProfileModel, AlarmProfile], AlarmProfileRepository
):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, AlarmProfileModel)

    async def find_default(self) -> AlarmProfile | None:
        return await self.find_by(is_default=True)

    def _to_domain(self, orm: AlarmProfileModel) -> AlarmProfile:
        return AlarmProfile(
            id=orm.id,
            name=orm.name,
            is_default=orm.is_default,
            intro_config=IntroConfig(sound_id=orm.intro_sound_id),
            sunrise_config=SunriseConfig(
                scene_id=orm.sunrise_scene_id,
                scene_name=orm.sunrise_scene_name,
                duration=timedelta(minutes=orm.sunrise_duration_minutes),
                brightness_start=orm.sunrise_brightness_start,
                brightness_end=orm.sunrise_brightness_end,
            ),
            ringtone_config=RingtoneConfig(
                sound_id=orm.ringtone_sound_id,
                volume=orm.ringtone_volume,
            ),
        )

    def _to_orm(self, domain: AlarmProfile) -> AlarmProfileModel:
        return AlarmProfileModel(
            id=domain.id,
            name=domain.name,
            is_default=domain.is_default,
            intro_sound_id=domain.intro_config.sound_id,
            sunrise_scene_id=domain.sunrise_config.scene_id,
            sunrise_scene_name=domain.sunrise_config.scene_name,
            sunrise_duration_minutes=domain.sunrise_config.duration_minutes,
            sunrise_brightness_start=domain.sunrise_config.brightness_start,
            sunrise_brightness_end=domain.sunrise_config.brightness_end,
            ringtone_sound_id=domain.ringtone_config.sound_id,
            ringtone_volume=domain.ringtone_config.volume,
        )


class SQLAlarmRepository(Repository[AlarmModel, Alarm], AlarmRepository):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, AlarmModel)

    async def find_enabled(self) -> list[Alarm]:
        return await self.find_all(is_enabled=True)

    def _to_domain(self, orm: AlarmModel) -> Alarm:
        return Alarm(
            id=orm.id,
            label=orm.label,
            is_enabled=orm.is_enabled,
            schedule=Schedule.from_mask(
                hour=orm.hour,
                minute=orm.minute,
                tz=ZoneInfo(orm.timezone),
                recurrence_mask=orm.recurrence_mask,
            ),
            profile_id=orm.profile_id,
            room_id=orm.room_id,
            room_name=orm.room_name,
            created_at=orm.created_at,
        )

    def _to_orm(self, domain: Alarm) -> AlarmModel:
        return AlarmModel(
            id=domain.id,
            label=domain.label,
            is_enabled=domain.is_enabled,
            hour=domain.schedule.hour,
            minute=domain.schedule.minute,
            timezone=domain.schedule.tz_name,
            recurrence_mask=domain.schedule.recurrence_mask,
            profile_id=domain.profile_id,
            room_id=domain.room_id,
            room_name=domain.room_name,
            created_at=domain.created_at,
        )


class SQLAlarmOccurrenceRepository(
    Repository[AlarmOccurrenceModel, AlarmOccurrence], AlarmOccurrenceRepository
):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, AlarmOccurrenceModel)

    async def find_for_alarm(
        self, alarm_id: UUID, limit: int = 20
    ) -> list[AlarmOccurrence]:
        stmt = (
            select(AlarmOccurrenceModel)
            .where(AlarmOccurrenceModel.alarm_id == alarm_id)
            .order_by(AlarmOccurrenceModel.scheduled_for.desc())
            .limit(limit)
        )
        result = await self.session.scalars(stmt)
        return [self._to_domain(orm) for orm in result.all()]

    async def find_active_for_alarm(self, alarm_id: UUID) -> AlarmOccurrence | None:
        stmt = (
            select(AlarmOccurrenceModel)
            .where(
                AlarmOccurrenceModel.alarm_id == alarm_id,
                AlarmOccurrenceModel.state.in_(_ACTIVE_STATES),
            )
            .order_by(AlarmOccurrenceModel.scheduled_for.desc())
            .limit(1)
        )
        orm = await self.session.scalar(stmt)
        return self._to_domain(orm) if orm is not None else None

    async def find_due(self, now: datetime) -> list[AlarmOccurrence]:
        stmt = (
            select(AlarmOccurrenceModel)
            .where(
                AlarmOccurrenceModel.state.in_(_WAITING_STATES),
                AlarmOccurrenceModel.scheduled_for <= now,
            )
            .order_by(AlarmOccurrenceModel.scheduled_for)
        )
        result = await self.session.scalars(stmt)
        return [self._to_domain(orm) for orm in result.all()]

    async def ensure_scheduled(
        self, alarm_id: UUID, scheduled_for: datetime
    ) -> AlarmOccurrence | None:
        """Insert the slot unless it exists. The unique constraint is the guard."""
        occurrence = AlarmOccurrence(alarm_id=alarm_id, scheduled_for=scheduled_for)
        try:
            async with self.session.begin_nested():
                self.session.add(self._to_orm(occurrence))
        except IntegrityError:
            return None
        return occurrence

    def _to_domain(self, orm: AlarmOccurrenceModel) -> AlarmOccurrence:
        return AlarmOccurrence(
            id=orm.id,
            alarm_id=orm.alarm_id,
            scheduled_for=orm.scheduled_for,
            state=OccurrenceState(orm.state),
            triggered_at=orm.triggered_at,
            finished_at=orm.finished_at,
            snooze_count=orm.snooze_count,
            failure_reason=orm.failure_reason,
        )

    def _to_orm(self, domain: AlarmOccurrence) -> AlarmOccurrenceModel:
        return AlarmOccurrenceModel(
            id=domain.id,
            alarm_id=domain.alarm_id,
            scheduled_for=domain.scheduled_for,
            state=domain.state.value,
            triggered_at=domain.triggered_at,
            finished_at=domain.finished_at,
            snooze_count=domain.snooze_count,
            failure_reason=domain.failure_reason,
        )
