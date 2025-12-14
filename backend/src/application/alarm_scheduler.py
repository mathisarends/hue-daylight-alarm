from datetime import datetime
from uuid import UUID

from backend.src.domain.aggregates import SunriseAlarm


class AlarmScheduler:
    def __init__(self):
        self._scheduled_alarms: dict[UUID, SunriseAlarm] = {}
        self._triggered_alarms: set[UUID] = set()

    def register_alarm(self, alarm: SunriseAlarm) -> None:
        if alarm.scheduled_time is None:
            raise ValueError("Cannot register alarm without scheduled_time")

        self._scheduled_alarms[alarm.id] = alarm

    def unregister_alarm(self, alarm_id: UUID) -> None:
        self._scheduled_alarms.pop(alarm_id, None)
        self._triggered_alarms.discard(alarm_id)

    def check_and_trigger_alarms(self) -> list[SunriseAlarm]:
        triggered = []
        current_time = datetime.now()
        current_hour = current_time.hour
        current_minute = current_time.minute

        for alarm_id, alarm in list(self._scheduled_alarms.items()):
            if alarm_id in self._triggered_alarms:
                continue

            scheduled = alarm.scheduled_time
            if scheduled is None:
                continue

            if scheduled.hour == current_hour and scheduled.minute == current_minute:
                try:
                    alarm.trigger()
                    triggered.append(alarm)
                    self._triggered_alarms.add(alarm_id)
                except ValueError:
                    pass

        return triggered

    def reset_daily_triggers(self) -> None:
        self._triggered_alarms.clear()

    def get_active_alarms(self) -> list[SunriseAlarm]:
        return list(self._scheduled_alarms.values())

    def get_alarm_by_id(self, alarm_id: UUID) -> SunriseAlarm | None:
        return self._scheduled_alarms.get(alarm_id)
