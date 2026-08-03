from datetime import datetime, timedelta, timezone
from uuid import uuid4

from huerise.features.alarm.domain import (
    Alarm,
    AlarmOccurrence,
    IntroConfig,
    OccurrenceState,
    RingtoneConfig,
    Schedule,
    SunriseConfig,
    Weekday,
)
from huerise.features.alarm.presentation.mappers import (
    alarm_to_read,
    intro_to_schema,
    occurrence_to_read,
    profile_to_read,
    ringtone_to_schema,
    schedule_to_schema,
    sunrise_to_schema,
)
from tests.application.conftest import make_profile


class TestScheduleToSchema:
    def test_carries_the_schedule_fields(self) -> None:
        schedule = Schedule(hour=6, minute=45, weekdays=frozenset({Weekday.MON}))

        schema = schedule_to_schema(schedule)

        assert schema.hour == 6
        assert schema.minute == 45
        assert schema.timezone == schedule.tz_name
        assert schema.days == [Weekday.MON]


class TestSunriseToSchema:
    def test_carries_the_sunrise_fields(self) -> None:
        config = SunriseConfig(duration=timedelta(minutes=15), brightness_start=5)

        schema = sunrise_to_schema(config)

        assert schema.scene_name == config.scene_name
        assert schema.duration_minutes == 15
        assert schema.brightness_start == 5
        assert schema.brightness_end == config.brightness_end


class TestRingtoneToSchema:
    def test_carries_the_ringtone_fields(self) -> None:
        config = RingtoneConfig(audio_file="alarm.mp3", volume=42)

        schema = ringtone_to_schema(config)

        assert schema.audio_file == "alarm.mp3"
        assert schema.volume == 42


class TestIntroToSchema:
    def test_carries_the_audio_file(self) -> None:
        config = IntroConfig(audio_file="intro.mp3")

        schema = intro_to_schema(config)

        assert schema.audio_file == "intro.mp3"


class TestAlarmToRead:
    def test_carries_the_alarm_fields(self) -> None:
        profile_id = uuid4()
        alarm = Alarm(
            label="Work",
            schedule=Schedule(hour=6, minute=45, weekdays=frozenset({Weekday.MON})),
            profile_id=profile_id,
            room_name="Bedroom",
        )

        read = alarm_to_read(alarm)

        assert read.id == alarm.id
        assert read.label == "Work"
        assert read.room_name == "Bedroom"
        assert read.profile_id == profile_id
        assert read.is_enabled is True
        assert read.created_at == alarm.created_at
        assert read.schedule.days == [Weekday.MON]
        assert read.next_occurrence == alarm.next_occurrence()

    def test_disabled_alarm_has_no_next_occurrence(self) -> None:
        alarm = Alarm(
            label="Work",
            schedule=Schedule(hour=6, minute=45),
            profile_id=uuid4(),
            room_name="Bedroom",
            is_enabled=False,
        )

        assert alarm_to_read(alarm).next_occurrence is None


class TestProfileToRead:
    def test_carries_the_nested_configs(self) -> None:
        profile = make_profile()

        read = profile_to_read(profile)

        assert read.id == profile.id
        assert read.name == profile.name
        assert read.is_default == profile.is_default
        assert read.intro.audio_file == profile.intro_config.audio_file
        assert read.ringtone.volume == profile.ringtone_config.volume
        assert read.sunrise.duration_minutes == 7


class TestOccurrenceToRead:
    def test_carries_the_occurrence_fields(self) -> None:
        alarm_id = uuid4()
        occurrence = AlarmOccurrence(
            alarm_id=alarm_id,
            scheduled_for=datetime(2026, 1, 1, 6, 45, tzinfo=timezone.utc),
            state=OccurrenceState.SNOOZED,
            snooze_count=2,
        )

        read = occurrence_to_read(occurrence)

        assert read.id == occurrence.id
        assert read.alarm_id == alarm_id
        assert read.scheduled_for == occurrence.scheduled_for
        assert read.state == OccurrenceState.SNOOZED
        assert read.triggered_at is None
        assert read.finished_at is None
        assert read.snooze_count == 2
        assert read.failure_reason is None
