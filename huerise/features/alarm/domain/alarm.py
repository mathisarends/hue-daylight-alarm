import uuid
from datetime import datetime, timedelta, timezone

from huerise.features.alarm.domain.exceptions import (
    AlarmAlreadyCancelledError,
    AlarmAlreadyInStatusError,
    AlarmNotRunningError,
)
from huerise.features.alarm.domain.views import (
    AlarmStatus,
    AlarmType,
    IntroConfig,
    RingtoneConfig,
    Schedule,
    SunriseConfig,
    Weekday,
)

_RUNNING_STATUSES = {AlarmStatus.INTRO, AlarmStatus.SUNRISE, AlarmStatus.RINGING}


class Alarm:
    def __init__(
        self,
        label: str,
        schedule: Schedule,
        status: AlarmStatus,
        alarm_type: AlarmType,
        series_id: uuid.UUID | None,
        intro_config: IntroConfig,
        sunrise_config: SunriseConfig,
        ringtone_config: RingtoneConfig,
        id: uuid.UUID | None = None,
        created_at: datetime | None = None,
    ) -> None:
        self.id = id if id is not None else uuid.uuid4()
        self.label = label
        self.schedule = schedule
        self.status = status
        self.alarm_type = alarm_type
        self.series_id = series_id
        self.intro_config = intro_config
        self.sunrise_config = sunrise_config
        self.ringtone_config = ringtone_config
        self.created_at = (
            created_at if created_at is not None else datetime.now(timezone.utc)
        )

    @property
    def is_running(self) -> bool:
        return self.status in _RUNNING_STATUSES

    @property
    def is_finished(self) -> bool:
        return self.status in {AlarmStatus.COMPLETED, AlarmStatus.CANCELLED}

    def trigger(self) -> None:
        if self.status != AlarmStatus.SCHEDULED:
            raise ValueError(f"Cannot trigger from status {self.status}")
        self.status = AlarmStatus.SUNRISE

    def ring(self) -> None:
        if self.status != AlarmStatus.SUNRISE:
            raise ValueError(f"Cannot ring from status {self.status}")
        self.status = AlarmStatus.RINGING

    def complete(self) -> None:
        if self.status != AlarmStatus.RINGING:
            raise ValueError(f"Cannot complete alarm from status {self.status}")
        self.status = AlarmStatus.COMPLETED

    def activate(self) -> None:
        if self.status != AlarmStatus.INACTIVE:
            raise AlarmAlreadyInStatusError(self.id, self.status)
        self.status = AlarmStatus.SCHEDULED

    def deactivate(self) -> None:
        if self.status != AlarmStatus.SCHEDULED:
            raise AlarmAlreadyInStatusError(self.id, self.status)
        self.status = AlarmStatus.INACTIVE

    def cancel(self) -> None:
        if not self._can_cancel():
            raise AlarmAlreadyCancelledError(self.id)
        self.status = AlarmStatus.CANCELLED

    def _can_cancel(self) -> bool:
        return self.status in {AlarmStatus.SCHEDULED, *_RUNNING_STATUSES}

    def snooze(self, minutes: int = 10) -> None:
        if not self.is_running:
            raise AlarmNotRunningError(self.id)

        wake_time = datetime.now(timezone.utc) + timedelta(minutes=minutes)
        self.schedule = Schedule(
            hour=wake_time.hour,
            minute=wake_time.minute,
            recurrence=self.schedule.recurrence,
        )
        self.status = AlarmStatus.SCHEDULED

    @classmethod
    def create_one_time(
        cls,
        label: str,
        hour: int,
        minute: int,
        room_name: str,
        intro_audio_file: str = "wake-up-bowls.mp3",
        ringtone_audio_file: str = "get-up-aurora.mp3",
    ) -> "Alarm":
        return cls(
            label=label,
            schedule=Schedule(hour=hour, minute=minute),
            status=AlarmStatus.SCHEDULED,
            alarm_type=AlarmType.ONE_TIME,
            series_id=None,
            intro_config=IntroConfig(audio_file=intro_audio_file),
            sunrise_config=SunriseConfig(room_name=room_name),
            ringtone_config=RingtoneConfig(audio_file=ringtone_audio_file),
        )

    @classmethod
    def create_recurring(
        cls,
        label: str,
        hour: int,
        minute: int,
        days: set["Weekday"],
        series_id: uuid.UUID,
        room_name: str,
        intro_audio_file: str = "wake-up-bowls.mp3",
        ringtone_audio_file: str = "get-up-aurora.mp3",
    ) -> "Alarm":
        return cls(
            label=label,
            schedule=Schedule(hour=hour, minute=minute, recurrence=frozenset(days)),
            status=AlarmStatus.SCHEDULED,
            alarm_type=AlarmType.RECURRING,
            series_id=series_id,
            intro_config=IntroConfig(audio_file=intro_audio_file),
            sunrise_config=SunriseConfig(room_name=room_name),
            ringtone_config=RingtoneConfig(audio_file=ringtone_audio_file),
        )
