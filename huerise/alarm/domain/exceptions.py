import uuid

from huerise.alarm.domain.views import AlarmStatus


class HueriseError(Exception):
    """Base for all domain exceptions."""


class AlarmNotFoundError(HueriseError):
    def __init__(self, alarm_id: uuid.UUID) -> None:
        super().__init__(f"Alarm {alarm_id} not found")


class AlarmAlreadyCancelledError(HueriseError):
    def __init__(self, alarm_id: uuid.UUID) -> None:
        super().__init__(f"Alarm {alarm_id} is already cancelled")


class AlarmAlreadyInStatusError(HueriseError):
    def __init__(self, alarm_id: uuid.UUID, status: AlarmStatus) -> None:
        super().__init__(f"Alarm {alarm_id} is already {status}")


class AlarmNotRunningError(HueriseError):
    def __init__(self, alarm_id: uuid.UUID) -> None:
        super().__init__(f"Alarm {alarm_id} is not currently running")
