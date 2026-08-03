import logging
from uuid import UUID
from zoneinfo import ZoneInfo

from huerise.features.alarm.application.ports import AudioPlayer
from huerise.features.alarm.domain import (
    DEFAULT_TIMEZONE,
    Alarm,
    AlarmNotFoundError,
    AlarmOccurrence,
    AlarmOccurrenceRepository,
    AlarmProfile,
    AlarmProfileNotFoundError,
    AlarmProfileRepository,
    AlarmRepository,
    NoActiveOccurrenceError,
    Schedule,
    Weekday,
)

logger = logging.getLogger(__name__)


class AlarmService:
    def __init__(
        self,
        alarms: AlarmRepository,
        profiles: AlarmProfileRepository,
        occurrences: AlarmOccurrenceRepository,
        audio: AudioPlayer,
    ) -> None:
        self._alarms = alarms
        self._profiles = profiles
        self._occurrences = occurrences
        self._audio = audio

    async def list_alarms(self) -> list[Alarm]:
        return await self._alarms.find_all()

    async def get_alarm(self, alarm_id: UUID) -> Alarm:
        return await self._get_or_raise(alarm_id)

    async def create_alarm(
        self,
        label: str,
        hour: int,
        minute: int,
        room_name: str,
        weekdays: frozenset[Weekday] = frozenset(),
        tz: ZoneInfo = DEFAULT_TIMEZONE,
        profile_id: UUID | None = None,
    ) -> Alarm:
        """Create a wake-up rule. Without weekdays it fires once and disables itself."""
        profile = await self._resolve_profile(profile_id)

        logger.info(
            "Creating alarm '%s' at %02d:%02d %s (%s)",
            label,
            hour,
            minute,
            tz.key,
            "recurring" if weekdays else "one-time",
        )
        alarm = Alarm(
            label=label,
            schedule=Schedule(hour=hour, minute=minute, tz=tz, weekdays=weekdays),
            profile_id=profile.id,
            room_name=room_name,
        )
        return await self._alarms.save(alarm)

    async def enable(self, alarm_id: UUID) -> Alarm:
        logger.info("Enabling alarm %s", alarm_id)
        alarm = await self._get_or_raise(alarm_id)
        alarm.enable()
        return await self._alarms.save(alarm)

    async def disable(self, alarm_id: UUID) -> Alarm:
        logger.info("Disabling alarm %s", alarm_id)
        alarm = await self._get_or_raise(alarm_id)
        alarm.disable()
        await self._cancel_active_occurrence(alarm_id)
        return await self._alarms.save(alarm)

    async def delete(self, alarm_id: UUID) -> None:
        logger.info("Deleting alarm %s", alarm_id)
        if not await self._alarms.delete_by_id(alarm_id):
            raise AlarmNotFoundError(alarm_id)

    async def list_occurrences(
        self, alarm_id: UUID, limit: int = 20
    ) -> list[AlarmOccurrence]:
        await self._get_or_raise(alarm_id)
        return await self._occurrences.find_for_alarm(alarm_id, limit=limit)

    async def snooze(self, alarm_id: UUID, minutes: int = 10) -> AlarmOccurrence:
        logger.info("Snoozing alarm %s for %d minutes", alarm_id, minutes)
        occurrence = await self._get_active_or_raise(alarm_id)
        occurrence.snooze(minutes)
        await self._audio.stop()
        return await self._occurrences.save(occurrence)

    async def dismiss(self, alarm_id: UUID) -> AlarmOccurrence:
        logger.info("Dismissing alarm %s", alarm_id)
        occurrence = await self._get_active_or_raise(alarm_id)
        occurrence.dismiss()
        await self._audio.stop()
        return await self._occurrences.save(occurrence)

    async def set_volume(self, volume: int) -> None:
        logger.info("Setting volume to %d", volume)
        await self._audio.set_volume(volume)

    async def _resolve_profile(self, profile_id: UUID | None) -> AlarmProfile:
        profile = (
            await self._profiles.find_by_id(profile_id)
            if profile_id is not None
            else await self._profiles.find_default()
        )
        if profile is None:
            raise AlarmProfileNotFoundError(profile_id)
        return profile

    async def _cancel_active_occurrence(self, alarm_id: UUID) -> None:
        occurrence = await self._occurrences.find_active_for_alarm(alarm_id)
        if occurrence is None:
            return
        if occurrence.is_running:
            occurrence.dismiss()
            await self._audio.stop()
        else:
            occurrence.skip()
        await self._occurrences.save(occurrence)

    async def _get_or_raise(self, alarm_id: UUID) -> Alarm:
        alarm = await self._alarms.find_by_id(alarm_id)
        if alarm is None:
            raise AlarmNotFoundError(alarm_id)
        return alarm

    async def _get_active_or_raise(self, alarm_id: UUID) -> AlarmOccurrence:
        await self._get_or_raise(alarm_id)
        occurrence = await self._occurrences.find_active_for_alarm(alarm_id)
        if occurrence is None:
            raise NoActiveOccurrenceError(alarm_id)
        return occurrence
