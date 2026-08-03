import uuid
from datetime import timezone

import pytest

from huerise.alarm.domain import (
    Alarm,
    AlarmAlreadyCancelledError,
    AlarmAlreadyInStatusError,
    AlarmNotRunningError,
    AlarmStatus,
    AlarmType,
    IntroConfig,
    RingtoneConfig,
    Schedule,
    SunriseConfig,
    Weekday,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _one_time(**kwargs) -> Alarm:
    defaults = dict(
        label="Test",
        hour=8,
        minute=0,
        room_name="Bedroom",
        intro_audio_file="intro.mp3",
        ringtone_audio_file="alarm.mp3",
    )
    defaults.update(kwargs)
    return Alarm.create_one_time(**defaults)


def _recurring(**kwargs) -> Alarm:
    defaults = dict(
        label="Test",
        hour=8,
        minute=0,
        days={Weekday.MON},
        series_id=uuid.uuid4(),
        room_name="Bedroom",
        intro_audio_file="intro.mp3",
        ringtone_audio_file="alarm.mp3",
    )
    defaults.update(kwargs)
    return Alarm.create_recurring(**defaults)


# ---------------------------------------------------------------------------
# Schedule
# ---------------------------------------------------------------------------


class TestScheduleValidation:
    def test_valid_schedule_stores_values(self) -> None:
        s = Schedule(hour=7, minute=30)
        assert s.hour == 7
        assert s.minute == 30

    def test_hour_below_zero_raises(self) -> None:
        with pytest.raises(ValueError, match="Hour must be 0-23"):
            Schedule(hour=-1, minute=0)

    def test_hour_above_23_raises(self) -> None:
        with pytest.raises(ValueError, match="Hour must be 0-23"):
            Schedule(hour=24, minute=0)

    def test_minute_below_zero_raises(self) -> None:
        with pytest.raises(ValueError, match="Minute must be 0-59"):
            Schedule(hour=0, minute=-1)

    def test_minute_above_59_raises(self) -> None:
        with pytest.raises(ValueError, match="Minute must be 0-59"):
            Schedule(hour=0, minute=60)

    def test_boundary_hour_zero_is_valid(self) -> None:
        s = Schedule(hour=0, minute=0)
        assert s.hour == 0

    def test_boundary_hour_23_is_valid(self) -> None:
        s = Schedule(hour=23, minute=59)
        assert s.hour == 23


class TestScheduleIsRecurring:
    def test_no_recurrence_is_not_recurring(self) -> None:
        s = Schedule(hour=8, minute=0)
        assert s.is_recurring() is False

    def test_with_recurrence_is_recurring(self) -> None:
        s = Schedule(hour=8, minute=0, recurrence=frozenset({Weekday.MON}))
        assert s.is_recurring() is True

    def test_empty_frozenset_recurrence_is_recurring(self) -> None:
        s = Schedule(hour=8, minute=0, recurrence=frozenset())
        assert s.is_recurring() is True


# ---------------------------------------------------------------------------
# Alarm factory methods
# ---------------------------------------------------------------------------


class TestCreateOneTime:
    def test_creates_alarm_with_correct_label(self) -> None:
        alarm = _one_time(label="Morning")
        assert alarm.label == "Morning"

    def test_creates_alarm_with_correct_schedule(self) -> None:
        alarm = _one_time(hour=7, minute=30)
        assert alarm.schedule.hour == 7
        assert alarm.schedule.minute == 30

    def test_creates_alarm_with_scheduled_status(self) -> None:
        alarm = _one_time()
        assert alarm.status == AlarmStatus.SCHEDULED

    def test_creates_alarm_with_one_time_type(self) -> None:
        alarm = _one_time()
        assert alarm.alarm_type == AlarmType.ONE_TIME

    def test_creates_alarm_with_no_series_id(self) -> None:
        alarm = _one_time()
        assert alarm.series_id is None

    def test_creates_alarm_with_uuid_id(self) -> None:
        alarm = _one_time()
        assert isinstance(alarm.id, uuid.UUID)

    def test_each_call_produces_unique_id(self) -> None:
        a1 = _one_time()
        a2 = _one_time()
        assert a1.id != a2.id

    def test_created_at_is_utc_aware(self) -> None:
        alarm = _one_time()
        assert alarm.created_at.tzinfo is not None
        assert alarm.created_at.tzinfo == timezone.utc

    def test_stores_intro_config(self) -> None:
        alarm = _one_time()
        assert alarm.intro_config.audio_file == "intro.mp3"

    def test_stores_sunrise_config(self) -> None:
        alarm = _one_time()
        assert alarm.sunrise_config.room_name == "Bedroom"

    def test_stores_ringtone_config(self) -> None:
        alarm = _one_time()
        assert alarm.ringtone_config.audio_file == "alarm.mp3"


class TestCreateRecurring:
    def test_creates_alarm_with_correct_label(self) -> None:
        alarm = _recurring(label="Weekdays")
        assert alarm.label == "Weekdays"

    def test_creates_alarm_with_recurring_type(self) -> None:
        alarm = _recurring()
        assert alarm.alarm_type == AlarmType.RECURRING

    def test_creates_alarm_with_scheduled_status(self) -> None:
        alarm = _recurring()
        assert alarm.status == AlarmStatus.SCHEDULED

    def test_stores_series_id(self) -> None:
        series = uuid.uuid4()
        alarm = _recurring(series_id=series)
        assert alarm.series_id == series

    def test_stores_days_as_frozenset_in_schedule(self) -> None:
        days = {Weekday.MON, Weekday.WED, Weekday.FRI}
        alarm = _recurring(days=days)
        assert alarm.schedule.recurrence == frozenset(days)

    def test_schedule_is_recurring(self) -> None:
        alarm = _recurring()
        assert alarm.schedule.is_recurring() is True


# ---------------------------------------------------------------------------
# Alarm.deactivate
# ---------------------------------------------------------------------------


class TestAlarmDeactivate:
    def test_scheduled_alarm_becomes_inactive(self) -> None:
        alarm = _one_time()
        alarm.deactivate()
        assert alarm.status == AlarmStatus.INACTIVE

    def test_deactivating_inactive_alarm_raises(self) -> None:
        alarm = _one_time()
        alarm.deactivate()
        with pytest.raises(AlarmAlreadyInStatusError, match="inactive"):
            alarm.deactivate()

    def test_deactivating_cancelled_alarm_raises(self) -> None:
        alarm = _one_time()
        alarm.cancel()
        with pytest.raises(AlarmAlreadyInStatusError, match="cancelled"):
            alarm.deactivate()


# ---------------------------------------------------------------------------
# Alarm.activate
# ---------------------------------------------------------------------------


class TestAlarmActivate:
    def _inactive_alarm(self) -> Alarm:
        alarm = _one_time()
        alarm.deactivate()
        return alarm

    def test_inactive_alarm_becomes_scheduled(self) -> None:
        alarm = self._inactive_alarm()
        alarm.activate()
        assert alarm.status == AlarmStatus.SCHEDULED

    def test_activating_scheduled_alarm_raises(self) -> None:
        alarm = _one_time()
        with pytest.raises(AlarmAlreadyInStatusError, match="scheduled"):
            alarm.activate()

    def test_activating_cancelled_alarm_raises(self) -> None:
        alarm = _one_time()
        alarm.cancel()
        with pytest.raises(AlarmAlreadyInStatusError, match="cancelled"):
            alarm.activate()


# ---------------------------------------------------------------------------
# Alarm.cancel
# ---------------------------------------------------------------------------


class TestAlarmCancel:
    def test_scheduled_alarm_becomes_cancelled(self) -> None:
        alarm = _one_time()
        alarm.cancel()
        assert alarm.status == AlarmStatus.CANCELLED

    def test_inactive_alarm_cannot_be_cancelled(self) -> None:
        alarm = _one_time()
        alarm.deactivate()
        with pytest.raises(AlarmAlreadyCancelledError):
            alarm.cancel()

    def test_cancelling_already_cancelled_alarm_raises(self) -> None:
        alarm = _one_time()
        alarm.cancel()
        with pytest.raises(AlarmAlreadyCancelledError):
            alarm.cancel()


# ---------------------------------------------------------------------------
# Phase transitions
# ---------------------------------------------------------------------------


class TestPhaseTransitions:
    def test_trigger_sets_sunrise(self) -> None:
        alarm = _one_time()
        alarm.trigger()
        assert alarm.status == AlarmStatus.SUNRISE

    def test_sunrise_to_ringing(self) -> None:
        alarm = _one_time()
        alarm.trigger()
        alarm.ring()
        assert alarm.status == AlarmStatus.RINGING

    def test_ringing_to_completed(self) -> None:
        alarm = _one_time()
        alarm.trigger()
        alarm.ring()
        alarm.complete()
        assert alarm.status == AlarmStatus.COMPLETED

    def test_trigger_from_wrong_status_raises(self) -> None:
        alarm = _one_time()
        alarm.trigger()
        with pytest.raises(ValueError):
            alarm.trigger()

    def test_ring_from_wrong_status_raises(self) -> None:
        alarm = _one_time()
        with pytest.raises(ValueError):
            alarm.ring()

    def test_complete_from_wrong_status_raises(self) -> None:
        alarm = _one_time()
        with pytest.raises(ValueError):
            alarm.complete()


# ---------------------------------------------------------------------------
# Alarm.snooze
# ---------------------------------------------------------------------------


class TestAlarmSnooze:
    def test_snooze_from_ringing_sets_status_to_scheduled(self) -> None:
        alarm = _one_time()
        alarm.trigger()
        alarm.ring()
        alarm.snooze(minutes=10)
        assert alarm.status == AlarmStatus.SCHEDULED

    def test_snooze_from_sunrise_sets_status_to_scheduled(self) -> None:
        alarm = _one_time()
        alarm.trigger()
        alarm.snooze(minutes=5)
        assert alarm.status == AlarmStatus.SCHEDULED

    def test_snooze_updates_schedule(self) -> None:
        alarm = _one_time(hour=7, minute=0)
        alarm.trigger()
        alarm.ring()
        alarm.snooze(minutes=10)
        assert alarm.schedule.hour != 7 or alarm.schedule.minute != 0

    def test_snooze_from_scheduled_raises(self) -> None:
        alarm = _one_time()
        with pytest.raises(AlarmNotRunningError):
            alarm.snooze()

    def test_snooze_from_inactive_raises(self) -> None:
        alarm = _one_time()
        alarm.deactivate()
        with pytest.raises(AlarmNotRunningError):
            alarm.snooze()

    def test_snooze_from_completed_raises(self) -> None:
        alarm = _one_time()
        alarm.trigger()
        alarm.ring()
        alarm.complete()
        with pytest.raises(AlarmNotRunningError):
            alarm.snooze()


# ---------------------------------------------------------------------------
# Derived state
# ---------------------------------------------------------------------------


class TestDerivedState:
    def test_is_running_false_when_scheduled(self) -> None:
        alarm = _one_time()
        assert alarm.is_running is False

    def test_is_running_true_when_sunrise(self) -> None:
        alarm = _one_time()
        alarm.trigger()
        assert alarm.is_running is True

    def test_is_running_true_when_ringing(self) -> None:
        alarm = _one_time()
        alarm.trigger()
        alarm.ring()
        assert alarm.is_running is True

    def test_is_finished_false_when_scheduled(self) -> None:
        alarm = _one_time()
        assert alarm.is_finished is False

    def test_is_finished_true_when_completed(self) -> None:
        alarm = _one_time()
        alarm.trigger()
        alarm.ring()
        alarm.complete()
        assert alarm.is_finished is True

    def test_is_finished_true_when_cancelled(self) -> None:
        alarm = _one_time()
        alarm.cancel()
        assert alarm.is_finished is True


# ---------------------------------------------------------------------------
# IntroConfig validation
# ---------------------------------------------------------------------------


class TestIntroConfig:
    def test_valid_config(self) -> None:
        cfg = IntroConfig(audio_file="intro.mp3")
        assert cfg.audio_file == "intro.mp3"


# ---------------------------------------------------------------------------
# SunriseConfig validation
# ---------------------------------------------------------------------------


class TestSunriseConfig:
    def test_valid_config(self) -> None:
        cfg = SunriseConfig(room_name="Bedroom")
        assert cfg.room_name == "Bedroom"

    def test_step_interval_calculation(self) -> None:
        cfg = SunriseConfig(room_name="Bedroom", duration_minutes=7, steps=70)
        assert cfg.step_interval_seconds == pytest.approx(6.0)

    def test_invalid_brightness_range_raises(self) -> None:
        with pytest.raises(ValueError, match="brightness"):
            SunriseConfig(room_name="Bedroom", brightness_start=50, brightness_end=30)

    def test_steps_zero_raises(self) -> None:
        with pytest.raises(ValueError, match="steps"):
            SunriseConfig(room_name="Bedroom", steps=0)


# ---------------------------------------------------------------------------
# RingtoneConfig validation
# ---------------------------------------------------------------------------


class TestRingtoneConfig:
    def test_valid_config(self) -> None:
        cfg = RingtoneConfig(audio_file="alarm.mp3", volume=80)
        assert cfg.volume == 80

    def test_volume_above_100_raises(self) -> None:
        with pytest.raises(ValueError, match="volume"):
            RingtoneConfig(audio_file="alarm.mp3", volume=101)

    def test_volume_below_0_raises(self) -> None:
        with pytest.raises(ValueError, match="volume"):
            RingtoneConfig(audio_file="alarm.mp3", volume=-1)
