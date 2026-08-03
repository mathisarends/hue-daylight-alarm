import logging
from collections.abc import Sequence
from uuid import UUID, uuid4

from huerise.features.alarm.domain import (
    Alarm,
    AlarmNotFoundError,
    AlarmRepository,
    Weekday,
)
from huerise.features.alarm.application.ports import AudioPlayer

logger = logging.getLogger(__name__)


class AlarmService:
    def __init__(self, alarm_repository: AlarmRepository, audio: AudioPlayer) -> None:
        self._alarm_repository = alarm_repository
        self._audio = audio

    async def list_alarms(self) -> Sequence[Alarm]:
        return await self._alarm_repository.get_all()

    async def create_one_time(
        self,
        label: str,
        hour: int,
        minute: int,
        room_name: str,
        intro_audio_file: str = "wake-up-bowls.mp3",
        ringtone_audio_file: str = "get-up-aurora.mp3",
    ) -> Alarm:
        logger.info("Creating one-time alarm '%s' at %02d:%02d", label, hour, minute)
        alarm = Alarm.create_one_time(
            label=label,
            hour=hour,
            minute=minute,
            room_name=room_name,
            intro_audio_file=intro_audio_file,
            ringtone_audio_file=ringtone_audio_file,
        )
        return await self._alarm_repository.save(alarm)

    async def create_recurring(
        self,
        label: str,
        hour: int,
        minute: int,
        days: frozenset[Weekday],
        room_name: str,
        intro_audio_file: str = "wake-up-bowls.mp3",
        ringtone_audio_file: str = "get-up-aurora.mp3",
    ) -> Alarm:
        logger.info("Creating recurring alarm '%s' at %02d:%02d", label, hour, minute)
        alarm = Alarm.create_recurring(
            label=label,
            hour=hour,
            minute=minute,
            days=set(days),
            series_id=uuid4(),
            room_name=room_name,
            intro_audio_file=intro_audio_file,
            ringtone_audio_file=ringtone_audio_file,
        )
        return await self._alarm_repository.save(alarm)

    async def activate(self, alarm_id: UUID) -> Alarm:
        logger.info("Activating alarm %s", alarm_id)
        alarm = await self._get_or_raise(alarm_id)
        alarm.activate()
        return await self._alarm_repository.save(alarm)

    async def deactivate(self, alarm_id: UUID) -> Alarm:
        logger.info("Deactivating alarm %s", alarm_id)
        alarm = await self._get_or_raise(alarm_id)
        alarm.deactivate()
        return await self._alarm_repository.save(alarm)

    async def cancel(self, alarm_id: UUID) -> Alarm:
        logger.info("Cancelling alarm %s", alarm_id)
        alarm = await self._get_or_raise(alarm_id)
        alarm.cancel()
        return await self._alarm_repository.save(alarm)

    async def snooze(self, alarm_id: UUID, minutes: int = 10) -> Alarm:
        logger.info("Snoozing alarm %s for %d minutes", alarm_id, minutes)
        alarm = await self._get_or_raise(alarm_id)
        alarm.snooze(minutes)
        await self._audio.stop()
        return await self._alarm_repository.save(alarm)

    async def delete(self, alarm_id: UUID) -> None:
        logger.info("Deleting alarm %s", alarm_id)
        await self._get_or_raise(alarm_id)
        await self._alarm_repository.delete(alarm_id)

    async def delete_series(self, series_id: UUID) -> None:
        logger.info("Deleting alarm series %s", series_id)
        alarms = await self._alarm_repository.get_all()
        series_alarms = [a for a in alarms if a.series_id == series_id]
        for alarm in series_alarms:
            await self._alarm_repository.delete(alarm.id)

    async def set_volume(self, volume: int) -> None:
        logger.info("Setting volume to %d", volume)
        await self._audio.set_volume(volume)

    async def _get_or_raise(self, alarm_id: UUID) -> Alarm:
        alarm = await self._alarm_repository.get(alarm_id)
        if alarm is None:
            raise AlarmNotFoundError(alarm_id)
        return alarm
