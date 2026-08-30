from datetime import UTC, datetime, timedelta

import pytest

from huerise.features.alarm.domain import AlarmDefect, OccurrenceState
from huerise.features.alarm.infrastructure.persistence import (
    SQLAlarmOccurrenceRepository,
    SQLAlarmProfileRepository,
    SQLAlarmRepository,
    SQLAlarmUnitOfWorkFactory,
)
from huerise.features.lighting.domain import HueBridgeSelection
from huerise.features.lighting.infrastructure.persistence import SQLHueBridgeRepository
from huerise.infrastructure.database.models import ALARM_DEFECTS, OCCURRENCE_STATES
from tests.application.conftest import make_alarm, make_occurrence, make_profile

NOW = datetime(2026, 8, 3, 5, 0, tzinfo=UTC)


def test_orm_states_match_the_domain_enum() -> None:
    assert tuple(state.value for state in OccurrenceState) == OCCURRENCE_STATES


def test_orm_defects_match_the_domain_enum() -> None:
    assert tuple(defect.value for defect in AlarmDefect) == ALARM_DEFECTS


class TestRoundtrip:
    async def test_hue_selection_keeps_credentials_and_replaces_address(
        self, session_factory
    ) -> None:
        repository = SQLHueBridgeRepository(session_factory)
        selected = HueBridgeSelection("bridge-1", "192.168.1.10", "secret-key")

        assert await repository.get_selected() is None
        await repository.save_selected(selected)
        await repository.save_selected(
            HueBridgeSelection("bridge-1", "192.168.1.11", "secret-key")
        )

        assert await repository.get_selected() == HueBridgeSelection(
            "bridge-1", "192.168.1.11", "secret-key"
        )

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

    async def test_alarm_defect_roundtrips_as_enum(self, session_factory) -> None:
        """A defect outlives the process: the bridge reports a deletion once."""
        profile = make_profile()
        alarm = make_alarm(profile_id=profile.id)
        alarm.set_defect(AlarmDefect.ROOM_MISSING)

        async with session_factory() as session:
            await SQLAlarmProfileRepository(session).save(profile)
            await SQLAlarmRepository(session).save(alarm)
            await session.commit()

        async with session_factory() as session:
            stored = await SQLAlarmRepository(session).find_by_id(alarm.id)

        assert stored is not None
        assert stored.defect is AlarmDefect.ROOM_MISSING
        assert stored.is_broken

    async def test_occurrence_state_roundtrips_as_enum(self, session_factory) -> None:
        profile = make_profile()
        alarm = make_alarm(profile_id=profile.id)
        occurrence = make_occurrence(alarm.id, NOW, OccurrenceState.SUNRISE)

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
        assert stored.state is OccurrenceState.SUNRISE
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
