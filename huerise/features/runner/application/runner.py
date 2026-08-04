import asyncio
import logging
from datetime import timedelta
from uuid import UUID

from huerise.features.alarm.domain import (
    Alarm,
    AlarmOccurrence,
    AlarmProfile,
    AlarmUnitOfWorkFactory,
    OccurrenceState,
)
from huerise.features.devices.application import AudioPlayer, Lights
from huerise.features.devices.domain import STEP_INTERVAL, SunriseRamp, sunrise_steps
from huerise.features.events.application import EventPublisher
from huerise.features.events.domain import (
    OccurrenceDismissed,
    OccurrenceFailed,
    OccurrenceProgress,
    OccurrenceRinging,
    OccurrenceSnapshot,
    OccurrenceStarted,
)
from huerise.features.runner.application.runner_port import (
    AlarmRunner as AlarmRunnerPort,
)

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
        events: EventPublisher,
        step_interval: timedelta = STEP_INTERVAL,
    ) -> None:
        self._lights = lights
        self._audio = audio
        self._unit_of_work_factory = unit_of_work_factory
        self._events = events
        self._step_interval = step_interval
        self._intro_tasks: set[asyncio.Task[None]] = set()

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
            await self._run_ringtone(occurrence, alarm, profile)
            await self._finish(occurrence.id)
        except Exception as error:
            logger.exception("Occurrence %s failed during execution", occurrence.id)
            await self._mark_failed(occurrence.id, repr(error))

    async def _run_sunrise(
        self, occurrence: AlarmOccurrence, alarm: Alarm, profile: AlarmProfile
    ) -> None:
        sunrise = profile.sunrise_config

        self._events.publish(
            OccurrenceStarted(
                occurrence=OccurrenceSnapshot.from_domain(occurrence),
                label=alarm.label,
                room_name=alarm.room_name,
                sunrise_seconds=round(sunrise.duration.total_seconds()),
            )
        )
        intro_task = asyncio.create_task(
            self._audio.play(profile.intro_config.sound_id, volume=INTRO_VOLUME)
        )
        self._intro_tasks.add(intro_task)
        intro_task.add_done_callback(self._intro_finished)
        await self._lights.activate_scene(
            sunrise.scene_id, brightness=sunrise.brightness_start
        )

        ramp = SunriseRamp(
            duration=sunrise.duration,
            brightness_start=sunrise.brightness_start,
            brightness_end=sunrise.brightness_end,
        )
        for step in sunrise_steps(ramp, self._step_interval):
            if not await self._still_in_state(occurrence.id, OccurrenceState.SUNRISE):
                logger.info("Sunrise for %s interrupted", occurrence.id)
                return
            await self._lights.set_brightness(alarm.room_id, step.brightness)
            self._events.publish(
                OccurrenceProgress(
                    occurrence_id=occurrence.id,
                    alarm_id=alarm.id,
                    brightness=step.brightness,
                    step=step.index,
                    total_steps=step.total,
                    elapsed_seconds=step.elapsed_seconds,
                    total_seconds=step.total_seconds,
                )
            )
            await asyncio.sleep(self._step_interval.total_seconds())

    def _intro_finished(self, task: asyncio.Task[None]) -> None:
        self._intro_tasks.discard(task)
        if task.cancelled():
            return
        try:
            task.result()
        except Exception:
            logger.exception("Intro playback failed")

    async def _run_ringtone(
        self, occurrence: AlarmOccurrence, alarm: Alarm, profile: AlarmProfile
    ) -> None:
        ringtone = profile.ringtone_config

        self._events.publish(
            OccurrenceRinging(
                occurrence_id=occurrence.id,
                alarm_id=alarm.id,
                sound_id=ringtone.sound_id,
                volume=ringtone.volume,
            )
        )
        await self._audio.stop()
        await self._audio.play(ringtone.sound_id, ringtone.volume)

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

        self._events.publish(
            OccurrenceDismissed(occurrence=OccurrenceSnapshot.from_domain(occurrence))
        )

    async def _mark_failed(self, occurrence_id: UUID, reason: str) -> None:
        async with self._unit_of_work_factory.create() as uow:
            occurrence = await uow.occurrences.find_by_id(occurrence_id)
            if occurrence is None or occurrence.is_finished:
                return
            occurrence.fail(reason)
            await uow.occurrences.save(occurrence)

        self._events.publish(
            OccurrenceFailed(occurrence=OccurrenceSnapshot.from_domain(occurrence))
        )
