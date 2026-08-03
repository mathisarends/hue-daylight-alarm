"""Translation from domain objects to their wire schemas."""

from huerise.features.alarm.domain import (
    Alarm,
    AlarmOccurrence,
    AlarmProfile,
    IntroConfig,
    RingtoneConfig,
    Schedule,
    SunriseConfig,
)
from huerise.features.alarm.presentation.schemas import (
    AlarmRead,
    IntroSchema,
    OccurrenceRead,
    ProfileRead,
    RingtoneSchema,
    ScheduleSchema,
    SunriseSchema,
)


def schedule_to_schema(schedule: Schedule) -> ScheduleSchema:
    return ScheduleSchema(
        hour=schedule.hour,
        minute=schedule.minute,
        timezone=schedule.tz_name,
        days=sorted(schedule.weekdays),
    )


def sunrise_to_schema(config: SunriseConfig) -> SunriseSchema:
    return SunriseSchema(
        scene_name=config.scene_name,
        duration_minutes=config.duration_minutes,
        brightness_start=config.brightness_start,
        brightness_end=config.brightness_end,
    )


def ringtone_to_schema(config: RingtoneConfig) -> RingtoneSchema:
    return RingtoneSchema(audio_file=config.audio_file, volume=config.volume)


def intro_to_schema(config: IntroConfig) -> IntroSchema:
    return IntroSchema(audio_file=config.audio_file)


def alarm_to_read(alarm: Alarm) -> AlarmRead:
    return AlarmRead(
        id=alarm.id,
        label=alarm.label,
        schedule=schedule_to_schema(alarm.schedule),
        room_name=alarm.room_name,
        profile_id=alarm.profile_id,
        is_enabled=alarm.is_enabled,
        created_at=alarm.created_at,
        next_occurrence=alarm.next_occurrence(),
    )


def profile_to_read(profile: AlarmProfile) -> ProfileRead:
    return ProfileRead(
        id=profile.id,
        name=profile.name,
        is_default=profile.is_default,
        intro=intro_to_schema(profile.intro_config),
        sunrise=sunrise_to_schema(profile.sunrise_config),
        ringtone=ringtone_to_schema(profile.ringtone_config),
    )


def occurrence_to_read(occurrence: AlarmOccurrence) -> OccurrenceRead:
    return OccurrenceRead(
        id=occurrence.id,
        alarm_id=occurrence.alarm_id,
        scheduled_for=occurrence.scheduled_for,
        state=occurrence.state,
        triggered_at=occurrence.triggered_at,
        finished_at=occurrence.finished_at,
        snooze_count=occurrence.snooze_count,
        failure_reason=occurrence.failure_reason,
    )
