from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel import SQLModel

from huerise.features.alarm.domain import OccurrenceState
from huerise.features.alarm.infrastructure.persistence import (
    SQLAlarmOccurrenceRepository,
    SQLAlarmProfileRepository,
    SQLAlarmRepository,
    SQLAlarmUnitOfWorkFactory,
)
from huerise.features.devices.domain import Sound, SoundCategory
from huerise.features.devices.infrastructure.persistence import SQLSoundRepository
from huerise.infrastructure.database.models import OCCURRENCE_STATES
from tests.application.conftest import make_alarm, make_occurrence, make_profile

NOW = datetime(2026, 8, 3, 5, 0, tzinfo=UTC)


@pytest_asyncio.fixture
async def session_factory() -> AsyncIterator[async_sessionmaker]:
    engine = create_async_engine("sqlite+aiosqlite://")
    async with engine.begin() as connection:
        await connection.run_sync(SQLModel.metadata.create_all)
    yield async_sessionmaker(engine, expire_on_commit=False)
    await engine.dispose()


def test_orm_states_match_the_domain_enum() -> None:
    assert tuple(state.value for state in OccurrenceState) == OCCURRENCE_STATES


class TestRoundtrip:
    async def test_sound_keeps_its_explicit_storage_metadata(
        self, session_factory
    ) -> None:
        sound = Sound(
            name="My own sound",
            category=SoundCategory.WAKE_UP,
            storage_path="sounds/custom/application-owned-key.mp3",
        )

        stored = await SQLSoundRepository(session_factory).save(sound)
        loaded = await SQLSoundRepository(session_factory).find_by_id(sound.id)

        assert loaded is not None
        assert loaded.id == stored.id
        assert loaded.name == "My own sound"
        assert loaded.storage_path == "sounds/custom/application-owned-key.mp3"
        assert loaded.created_at == sound.created_at

    async def test_alarm_keeps_timezone_and_recurrence(self, session_factory) -> None:
        profile = make_profile()
        alarm = make_alarm(hour=6, minute=45, profile_id=profile.id)

        async with session_factory() as session:
            await SQLAlarmProfileRepository(session).save(profile)
            await SQLAlarmRepository(session).save(alarm)
            await session.commit()

        async with session_factory() as session:
            stored = await SQLAlarmRepository(session).find_by_id(alarm.id)

        assert stored is not None
        assert stored.schedule == alarm.schedule
        assert stored.schedule.tz_name == "Europe/Berlin"

    async def test_created_at_stays_timezone_aware(self, session_factory) -> None:
        """SQLite hands back naive datetimes unless the column type intervenes."""
        profile = make_profile()
        alarm = make_alarm(profile_id=profile.id)

        async with session_factory() as session:
            await SQLAlarmProfileRepository(session).save(profile)
            await SQLAlarmRepository(session).save(alarm)
            await session.commit()

        async with session_factory() as session:
            stored = await SQLAlarmRepository(session).find_by_id(alarm.id)

        assert stored is not None
        assert stored.created_at.tzinfo is not None
        assert stored.created_at == alarm.created_at

    async def test_occurrence_state_roundtrips_as_enum(self, session_factory) -> None:
        profile = make_profile()
        alarm = make_alarm(profile_id=profile.id)
        occurrence = make_occurrence(alarm.id, NOW, OccurrenceState.SNOOZED)

        async with session_factory() as session:
            await SQLAlarmProfileRepository(session).save(profile)
            await SQLAlarmRepository(session).save(alarm)
            await SQLAlarmOccurrenceRepository(session).save(occurrence)
            await session.commit()

        async with session_factory() as session:
            stored = await SQLAlarmOccurrenceRepository(session).find_by_id(
                occurrence.id
            )

        assert stored is not None
        assert stored.state is OccurrenceState.SNOOZED
        assert stored.scheduled_for == NOW


class TestEnsureScheduled:
    @pytest.fixture(autouse=True)
    async def _seed(self, session_factory):
        self.profile = make_profile()
        self.alarm = make_alarm(profile_id=self.profile.id)
        async with session_factory() as session:
            await SQLAlarmProfileRepository(session).save(self.profile)
            await SQLAlarmRepository(session).save(self.alarm)
            await session.commit()

    async def test_creates_the_slot_once(self, session_factory) -> None:
        async with session_factory() as session:
            repository = SQLAlarmOccurrenceRepository(session)
            first = await repository.ensure_scheduled(self.alarm.id, NOW)
            second = await repository.ensure_scheduled(self.alarm.id, NOW)
            await session.commit()

        assert first is not None
        assert second is None

    async def test_is_idempotent_across_sessions(self, session_factory) -> None:
        async with session_factory() as session:
            await SQLAlarmOccurrenceRepository(session).ensure_scheduled(
                self.alarm.id, NOW
            )
            await session.commit()

        async with session_factory() as session:
            repeated = await SQLAlarmOccurrenceRepository(session).ensure_scheduled(
                self.alarm.id, NOW
            )
            await session.commit()

        assert repeated is None

    async def test_a_different_slot_is_created(self, session_factory) -> None:
        async with session_factory() as session:
            repository = SQLAlarmOccurrenceRepository(session)
            await repository.ensure_scheduled(self.alarm.id, NOW)
            later = await repository.ensure_scheduled(
                self.alarm.id, NOW + timedelta(days=1)
            )
            await session.commit()

        assert later is not None


class TestUnitOfWork:
    async def test_commits_on_success(self, session_factory) -> None:
        factory = SQLAlarmUnitOfWorkFactory(session_factory)
        profile = make_profile()

        async with factory.create() as uow:
            await uow.profiles.save(profile)

        async with session_factory() as session:
            stored = await SQLAlarmProfileRepository(session).find_default()

        assert stored is not None
        assert stored.id == profile.id

    async def test_rolls_back_on_error(self, session_factory) -> None:
        factory = SQLAlarmUnitOfWorkFactory(session_factory)

        with pytest.raises(RuntimeError):
            async with factory.create() as uow:
                await uow.profiles.save(make_profile())
                raise RuntimeError("boom")

        async with session_factory() as session:
            stored = await SQLAlarmProfileRepository(session).find_all()

        assert stored == []
