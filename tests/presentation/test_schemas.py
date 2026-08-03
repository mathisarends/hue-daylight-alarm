from datetime import timedelta
from uuid import uuid4

import pytest
from pydantic import ValidationError

from huerise.features.alarm.domain import Alarm, Schedule, SunriseConfig, Weekday
from huerise.features.alarm.presentation.mappers import (
    alarm_to_read,
    profile_to_read,
    schedule_to_schema,
    sunrise_to_schema,
)
from huerise.features.alarm.presentation.schemas import ScheduleSchema
from tests.application.conftest import make_profile


class TestScheduleSchema:
    def test_roundtrips_through_the_domain(self) -> None:
        schema = ScheduleSchema(
            hour=6, minute=45, timezone="Europe/Berlin", days=[Weekday.MON]
        )

        assert schedule_to_schema(schema.to_domain()) == schema

    def test_defaults_to_a_one_time_schedule(self) -> None:
        schedule = ScheduleSchema(hour=7, minute=0).to_domain()

        assert schedule.is_recurring is False
        assert schedule.tz_name == "Europe/Berlin"

    def test_rejects_an_unknown_timezone(self) -> None:
        with pytest.raises(ValidationError):
            ScheduleSchema(hour=7, minute=0, timezone="Mars/Olympus")

    def test_rejects_an_impossible_time(self) -> None:
        with pytest.raises(ValidationError):
            ScheduleSchema(hour=24, minute=0)


class TestSunriseSchema:
    def test_roundtrips_through_the_domain(self) -> None:
        config = SunriseConfig(duration=timedelta(minutes=15), brightness_start=5)

        assert sunrise_to_schema(config).to_domain() == config


class TestAlarmRead:
    def test_exposes_the_next_occurrence(self) -> None:
        alarm = Alarm(
            label="Work",
            schedule=Schedule(hour=6, minute=45, weekdays=frozenset({Weekday.MON})),
            profile_id=uuid4(),
            room_name="Bedroom",
        )

        read = alarm_to_read(alarm)

        assert read.schedule.days == [Weekday.MON]
        assert read.next_occurrence is not None

    def test_disabled_alarm_has_no_next_occurrence(self) -> None:
        alarm = Alarm(
            label="Work",
            schedule=Schedule(hour=6, minute=45),
            profile_id=uuid4(),
            room_name="Bedroom",
            is_enabled=False,
        )

        assert alarm_to_read(alarm).next_occurrence is None


class TestProfileRead:
    def test_carries_the_nested_configs(self) -> None:
        profile = make_profile()

        read = profile_to_read(profile)

        assert read.intro.audio_file == profile.intro_config.audio_file
        assert read.ringtone.volume == profile.ringtone_config.volume
        assert read.sunrise.duration_minutes == 7
