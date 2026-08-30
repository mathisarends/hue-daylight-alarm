import asyncio
import logging
from datetime import timedelta
from uuid import UUID

from huerise.features.alarm.domain import (
    Alarm,
    AlarmDefect,
    AlarmField,
    AlarmOccurrence,
    AlarmProfile,
    AlarmUnitOfWorkFactory,
    OccurrenceState,
)
from huerise.features.events.application import EventPublisher
from huerise.features.events.domain import (
    AlarmSnapshot,
    AlarmUpdated,
    OccurrenceDismissed,
    OccurrenceFailed,
    OccurrenceProgress,
    OccurrenceSnapshot,
    OccurrenceStarted,
)
from huerise.features.lighting.application import Lights
from huerise.features.lighting.domain import (
    STEP_INTERVAL,
    RoomNotFoundError,
    Scene,
    SceneNotFoundError,
    SunriseRamp,
    sunrise_steps,
)
from huerise.features.runner.application.runner_port import (
    AlarmRunner as AlarmRunnerPort,
)

logger = logging.getLogger(__name__)


class AlarmRunner(AlarmRunnerPort):
    """Executes one occurrence: ramp the room up, then finish.

    The occurrence arrives already claimed (SUNRISE) by the scheduler. State is
    re-read between steps so a dismiss coming in over the API wins.
    """

    def __init__(
        self,
        lights: Lights,
        unit_of_work_factory: AlarmUnitOfWorkFactory,
        events: EventPublisher,
        step_interval: timedelta = STEP_INTERVAL,
    ) -> None:
        self._lights = lights
        self._unit_of_work_factory = unit_of_work_factory
        self._events = events
        self._step_interval = step_interval

    async def run(self, occurrence: AlarmOccurrence) -> None:
        try:
            context = await self._load(occurrence.alarm_id)
            if context is None:
                logger.error("Occurrence %s has no alarm to run", occurrence.id)
                return
            alarm, profile = context

            await self._light_up(occurrence, alarm, profile)
            await self._finish(occurrence.id)
        except Exception as error:
            logger.exception("Occurrence %s failed during execution", occurrence.id)
            await self._mark_failed(occurrence.id, repr(error))

    async def _light_up(
        self, occurrence: AlarmOccurrence, alarm: Alarm, profile: AlarmProfile
    ) -> None:
        """Run the sunrise, recording a defect rather than failing the run.

        A bridge that is down or a room somebody deleted must not cost the
        occurrence its finish -- it is recorded and the occurrence still ends.
        """
        try:
            await self._run_sunrise(occurrence, alarm, profile)
        except Exception as error:
            logger.exception(
                "Sunrise for %s failed, finishing without light", occurrence.id
            )
            await self._record_defect(alarm, error)

    async def _record_defect(self, alarm: Alarm, error: Exception) -> None:
        """Flag a room or scene that is not there, so it can be fixed by tomorrow.

        Anything else -- an unreachable bridge, a scene too dim to ramp -- is
        about this one run and says nothing about the rule.
        """
        defect = _defect_for(error)
        if defect is None:
            return

        async with self._unit_of_work_factory.create() as uow:
            stored = await uow.alarms.find_by_id(alarm.id)
            if stored is None or not stored.set_defect(defect):
                return
            stored = await uow.alarms.save(stored)

        self._events.publish(
            AlarmUpdated(
                alarm=AlarmSnapshot.from_domain(stored), changed=[AlarmField.DEFECT]
            )
        )

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
        scene = await self._get_scene(alarm.room_id, sunrise.scene_id)
        brightness_end = (
            round(scene.brightness)
            if scene.brightness is not None
            else sunrise.brightness_end
        )
        # A profile may impose a lower ceiling, but its default of 100% must
        # not make a dimmer Hue scene brighter than it was configured.
        brightness_end = min(brightness_end, sunrise.brightness_end)
        if brightness_end <= sunrise.brightness_start:
            raise ValueError(
                f"Scene '{scene.name}' brightness must be above the sunrise "
                f"start brightness ({sunrise.brightness_start}%)"
            )
        await self._lights.activate_scene(
            sunrise.scene_id, brightness=sunrise.brightness_start
        )

        ramp = SunriseRamp(
            duration=sunrise.duration,
            brightness_start=sunrise.brightness_start,
            brightness_end=brightness_end,
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

        # Group dimming flattens the individual light levels. A final recall
        # without an override restores the scene exactly as stored in Hue.
        await self._lights.activate_scene(sunrise.scene_id)

    async def _get_scene(self, room_id: UUID, scene_id: UUID) -> Scene:
        room = next(
            (room for room in await self._lights.list_rooms() if room.id == room_id),
            None,
        )
        if room is None:
            raise RoomNotFoundError(str(room_id))
        scene = next((scene for scene in room.scenes if scene.id == scene_id), None)
        if scene is None:
            raise SceneNotFoundError(str(room_id), str(scene_id))
        return scene

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


def _defect_for(error: Exception) -> AlarmDefect | None:
    match error:
        case RoomNotFoundError():
            return AlarmDefect.ROOM_MISSING
        case SceneNotFoundError():
            return AlarmDefect.SCENE_MISSING
        case _:
            return None
