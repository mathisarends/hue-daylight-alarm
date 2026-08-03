from huerise.features.alarm.domain import Alarm, AlarmOccurrence, AlarmProfile
from huerise.features.alarm.presentation.schemas import (
    AlarmOut,
    OccurrenceOut,
    ProfileOut,
    ScheduleOut,
)


def to_alarm_out(alarm: Alarm) -> AlarmOut:
    return AlarmOut(
        id=alarm.id,
        label=alarm.label,
        is_enabled=alarm.is_enabled,
        schedule=ScheduleOut(
            hour=alarm.schedule.hour,
            minute=alarm.schedule.minute,
            timezone=alarm.schedule.tz_name,
            days=sorted(alarm.schedule.weekdays),
        ),
        room_name=alarm.room_name,
        profile_id=alarm.profile_id,
        created_at=alarm.created_at,
        next_occurrence=alarm.next_occurrence(),
    )


def to_occurrence_out(occurrence: AlarmOccurrence) -> OccurrenceOut:
    return OccurrenceOut(
        id=occurrence.id,
        alarm_id=occurrence.alarm_id,
        scheduled_for=occurrence.scheduled_for,
        state=occurrence.state,
        triggered_at=occurrence.triggered_at,
        finished_at=occurrence.finished_at,
        snooze_count=occurrence.snooze_count,
        failure_reason=occurrence.failure_reason,
    )


def to_profile_out(profile: AlarmProfile) -> ProfileOut:
    return ProfileOut(
        id=profile.id,
        name=profile.name,
        is_default=profile.is_default,
        intro_audio_file=profile.intro_config.audio_file,
        scene_name=profile.sunrise_config.scene_name,
        sunrise_duration_minutes=profile.sunrise_config.duration_minutes,
        brightness_start=profile.sunrise_config.brightness_start,
        brightness_end=profile.sunrise_config.brightness_end,
        ringtone_audio_file=profile.ringtone_config.audio_file,
        ringtone_volume=profile.ringtone_config.volume,
    )
