from huerise.features.alarm.domain import Alarm
from huerise.features.alarm.presentation.schemas import AlarmOut, ScheduleOut


def to_alarm_out(alarm: Alarm) -> AlarmOut:
    return AlarmOut(
        id=alarm.id,
        label=alarm.label,
        schedule=ScheduleOut(
            hour=alarm.schedule.hour,
            minute=alarm.schedule.minute,
            recurrence=sorted(alarm.schedule.recurrence)
            if alarm.schedule.recurrence
            else None,
        ),
        status=alarm.status,
        alarm_type=alarm.alarm_type,
        series_id=alarm.series_id,
        created_at=alarm.created_at,
    )
