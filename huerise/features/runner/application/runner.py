import asyncio
import logging
from datetime import timedelta
from uuid import UUID

from huerise.features.alarm.application.ports import AudioPlayer
from huerise.features.alarm.domain import (
    Alarm,
    AlarmOccurrence,
    AlarmProfile,
    AlarmUnitOfWorkFactory,
    OccurrenceState,
)
from huerise.features.runner.application.ports import Lights
from huerise.features.runner.application.runner_port import (
    AlarmRunner as AlarmRunnerPort,
)
from huerise.features.runner.application.sunrise import STEP_INTERVAL, sunrise_steps

logger = logging.getLogger(__name__)

INTRO_VOLUME = 50


class AlarmRunner(AlarmRunnerPort):
    """Executes one occurrence: intro, sunrise, ringtone.

    The occurrence arrives already claimed (SUNRISE) by the scheduler. State is
    re-read between phases so a dismiss or snooze coming in over the API wins.
    """

    def __init__(
        self,
        lights: Lights,
        audio: AudioPlayer,
        unit_of_work_factory: AlarmUnitOfWorkFactory,
        step_interval: timedelta = STEP_INTERVAL,
    ) -> None:
        self._lights = lights
        self._audio = audio
        self._unit_of_work_factory = unit_of_work_factory
        self._step_interval = step_interval

    async def run(self, occurrence: AlarmOccurrence) -> None:
        try:
            context = await self._load(occurrence.alarm_id)
            if context is None:
                logger.error("Occurrence %s has no alarm to run", occurrence.id)
                return
            alarm, profile = context

            await self._run_sunrise(occurrence, alarm, profile)
            if not await self._start_ringing(occurrence.id):
                return
            await self._run_ringtone(profile)
            await self._finish(occurrence.id)
        except Exception as error:
            logger.exception("Occurrence %s failed during execution", occurrence.id)
            await self._mark_failed(occurrence.id, repr(error))

    async def _run_sunrise(
        self, occurrence: AlarmOccurrence, alarm: Alarm, profile: AlarmProfile
    ) -> None:
        sunrise = profile.sunrise_config

        asyncio.create_task(
            self._audio.play(profile.intro_config.audio_file, volume=INTRO_VOLUME)
        )
        await self._lights.activate_scene(alarm.room_name, sunrise.scene_name)

        for brightness in sunrise_steps(sunrise, self._step_interval):
            if not await self._still_in_state(occurrence.id, OccurrenceState.SUNRISE):
                logger.info("Sunrise for %s interrupted", occurrence.id)
                return
            await self._lights.set_brightness(alarm.room_name, brightness)
            await asyncio.sleep(self._step_interval.total_seconds())

    async def _run_ringtone(self, profile: AlarmProfile) -> None:
        ringtone = profile.ringtone_config
        await self._audio.stop()
        await self._audio.play(ringtone.audio_file, ringtone.volume)

    async def _load(self, alarm_id: UUID) -> tuple[Alarm, AlarmProfile] | None:
        async with self._unit_of_work_factory.create() as uow:
            alarm = await uow.alarms.find_by_id(alarm_id)
            if alarm is None:
                return None
            profile = await uow.profiles.find_by_id(alarm.profile_id)
            if profile is None:
                return None
            return alarm, profile

    async def _still_in_state(
        self, occurrence_id: UUID, state: OccurrenceState
    ) -> bool:
        async with self._unit_of_work_factory.create() as uow:
            occurrence = await uow.occurrences.find_by_id(occurrence_id)
            return occurrence is not None and occurrence.state is state

    async def _start_ringing(self, occurrence_id: UUID) -> bool:
        """False when the occurrence was dismissed or snoozed during sunrise."""
        async with self._unit_of_work_factory.create() as uow:
            occurrence = await uow.occurrences.find_by_id(occurrence_id)
            if occurrence is None or occurrence.state is not OccurrenceState.SUNRISE:
                return False
            occurrence.ring()
            await uow.occurrences.save(occurrence)
            return True

    async def _finish(self, occurrence_id: UUID) -> None:
        async with self._unit_of_work_factory.create() as uow:
            occurrence = await uow.occurrences.find_by_id(occurrence_id)
            if occurrence is None or not occurrence.is_running:
                return
            occurrence.dismiss()
            await uow.occurrences.save(occurrence)

    async def _mark_failed(self, occurrence_id: UUID, reason: str) -> None:
        async with self._unit_of_work_factory.create() as uow:
            occurrence = await uow.occurrences.find_by_id(occurrence_id)
            if occurrence is None or occurrence.is_finished:
                return
            occurrence.fail(reason)
            await uow.occurrences.save(occurrence)
