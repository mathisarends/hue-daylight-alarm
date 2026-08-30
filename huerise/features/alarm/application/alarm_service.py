import logging
from uuid import UUID

from huerise.features.alarm.domain import (
    Alarm,
    AlarmField,
    AlarmNotFoundError,
    AlarmOccurrence,
    AlarmOccurrenceRepository,
    AlarmProfile,
    AlarmProfileNotFoundError,
    AlarmProfileRepository,
    AlarmRepository,
    NoActiveOccurrenceError,
    OccurrenceState,
    Schedule,
)
from huerise.features.events.application import EventPublisher
from huerise.features.events.domain import (
    AlarmCreated,
    AlarmDeleted,
    AlarmSnapshot,
    AlarmUpdated,
    OccurrenceDismissed,
    OccurrenceSkipped,
    OccurrenceSnapshot,
)
from huerise.features.lighting.application import Lights
from huerise.features.lighting.domain import RoomNotFoundError, SceneNotFoundError

logger = logging.getLogger(__name__)


class AlarmService:
    def __init__(
        self,
        alarms: AlarmRepository,
        profiles: AlarmProfileRepository,
        occurrences: AlarmOccurrenceRepository,
        lights: Lights,
        events: EventPublisher,
    ) -> None:
        self._alarms = alarms
        self._profiles = profiles
        self._occurrences = occurrences
        self._lights = lights
        self._events = events

    async def find_all(self) -> list[Alarm]:
        return await self._alarms.find_all()

    async def find_by_id(self, alarm_id: UUID) -> Alarm:
        alarm = await self._alarms.find_by_id(alarm_id)
        if alarm is None:
            raise AlarmNotFoundError(alarm_id)
        return alarm

    async def create(
        self,
        label: str,
        schedule: Schedule,
        room_id: UUID,
        room_name: str,
        profile_id: UUID | None = None,
    ) -> Alarm:
        """Create a wake-up rule. Without weekdays it fires once and disables itself."""
        profile = await self._resolve_profile(profile_id)
        await self._validate_scene(room_id, profile)

        logger.info(
            "Creating alarm '%s' at %02d:%02d %s (%s)",
            label,
            schedule.hour,
            schedule.minute,
            schedule.tz_name,
            "recurring" if schedule.is_recurring else "one-time",
        )
        alarm = Alarm(
            label=label,
            schedule=schedule,
            profile_id=profile.id,
            room_id=room_id,
            room_name=room_name,
        )
        alarm = await self._alarms.save(alarm)
        self._events.publish(AlarmCreated(alarm=AlarmSnapshot.from_domain(alarm)))
        return alarm

    async def update(
        self,
        alarm_id: UUID,
        label: str | None = None,
        schedule: Schedule | None = None,
        room_id: UUID | None = None,
        room_name: str | None = None,
        profile_id: UUID | None = None,
    ) -> Alarm:
        """Change a wake-up rule. Omitted fields keep their current value."""
        alarm = await self.find_by_id(alarm_id)
        revalidated = room_id is not None or profile_id is not None
        if revalidated:
            profile = await self._resolve_profile(profile_id or alarm.profile_id)
            await self._validate_scene(room_id or alarm.room_id, profile)

        changed = alarm.update(
            label=label,
            schedule=schedule,
            room_id=room_id,
            room_name=room_name,
            profile_id=profile_id,
        )
        # Room and scene were just checked against the bridge, so whatever the
        # bridge broke earlier is settled.
        if revalidated and alarm.set_defect(None):
            changed.append(AlarmField.DEFECT)
        if not changed:
            return alarm

        logger.info("Updating alarm %s (%s)", alarm_id, ", ".join(changed))
        if AlarmField.SCHEDULE in changed:
            await self._drop_pending_occurrence(alarm_id)

        alarm = await self._alarms.save(alarm)
        self._events.publish(
            AlarmUpdated(alarm=AlarmSnapshot.from_domain(alarm), changed=changed)
        )
        return alarm

    async def enable(self, alarm_id: UUID) -> Alarm:
        logger.info("Enabling alarm %s", alarm_id)
        alarm = await self.find_by_id(alarm_id)
        alarm.enable()

        alarm = await self._alarms.save(alarm)
        self._events.publish(
            AlarmUpdated(
                alarm=AlarmSnapshot.from_domain(alarm), changed=[AlarmField.IS_ENABLED]
            )
        )
        return alarm

    async def disable(self, alarm_id: UUID) -> Alarm:
        logger.info("Disabling alarm %s", alarm_id)
        alarm = await self.find_by_id(alarm_id)
        alarm.disable()
        await self._cancel_active_occurrence(alarm_id)

        alarm = await self._alarms.save(alarm)
        self._events.publish(
            AlarmUpdated(
                alarm=AlarmSnapshot.from_domain(alarm), changed=[AlarmField.IS_ENABLED]
            )
        )
        return alarm

    async def delete(self, alarm_id: UUID) -> None:
        logger.info("Deleting alarm %s", alarm_id)
        if not await self._alarms.delete_by_id(alarm_id):
            raise AlarmNotFoundError(alarm_id)
        self._events.publish(AlarmDeleted(alarm_id=alarm_id))

    async def list_occurrences(
        self, alarm_id: UUID, limit: int = 20
    ) -> list[AlarmOccurrence]:
        await self.find_by_id(alarm_id)
        return await self._occurrences.find_for_alarm(alarm_id, limit=limit)

    async def dismiss(self, alarm_id: UUID) -> AlarmOccurrence:
        logger.info("Dismissing alarm %s", alarm_id)
        occurrence = await self._get_active_or_raise(alarm_id)
        occurrence.dismiss()

        occurrence = await self._occurrences.save(occurrence)
        self._events.publish(
            OccurrenceDismissed(occurrence=OccurrenceSnapshot.from_domain(occurrence))
        )
        return occurrence

    async def _resolve_profile(self, profile_id: UUID | None) -> AlarmProfile:
        profile = (
            await self._profiles.find_by_id(profile_id)
            if profile_id is not None
            else await self._profiles.find_default()
        )
        if profile is None:
            raise AlarmProfileNotFoundError(profile_id)
        return profile

    async def _validate_scene(self, room_id: UUID, profile: AlarmProfile) -> None:
        room = next(
            (room for room in await self._lights.list_rooms() if room.id == room_id),
            None,
        )
        if room is None:
            raise RoomNotFoundError(str(room_id))
        scene = next(
            (
                scene
                for scene in room.scenes
                if scene.id == profile.sunrise_config.scene_id
            ),
            None,
        )
        if scene is None:
            raise SceneNotFoundError(str(room_id), str(profile.sunrise_config.scene_id))

        brightness = scene.brightness
        if (
            brightness is not None
            and round(brightness) <= profile.sunrise_config.brightness_start
        ):
            raise ValueError(
                f"Scene '{scene.name}' brightness must be above the sunrise "
                f"start brightness ({profile.sunrise_config.brightness_start}%)"
            )

    async def _drop_pending_occurrence(self, alarm_id: UUID) -> None:
        """Retire the run materialised for the old time, so it cannot still fire.

        Only a pending run is dropped. A sunrise already underway is about the
        current wake-up and outlives a change to tomorrow's schedule.
        """
        occurrence = await self._occurrences.find_active_for_alarm(alarm_id)
        if occurrence is None or occurrence.state is not OccurrenceState.PENDING:
            return
        occurrence.skip()
        occurrence = await self._occurrences.save(occurrence)
        self._events.publish(
            OccurrenceSkipped(occurrence=OccurrenceSnapshot.from_domain(occurrence))
        )

    async def _cancel_active_occurrence(self, alarm_id: UUID) -> None:
        occurrence = await self._occurrences.find_active_for_alarm(alarm_id)
        if occurrence is None:
            return

        if occurrence.is_running:
            occurrence.dismiss()
        else:
            occurrence.skip()

        occurrence = await self._occurrences.save(occurrence)
        snapshot = OccurrenceSnapshot.from_domain(occurrence)
        self._events.publish(
            OccurrenceDismissed(occurrence=snapshot)
            if occurrence.state is OccurrenceState.DISMISSED
            else OccurrenceSkipped(occurrence=snapshot)
        )

    async def _get_active_or_raise(self, alarm_id: UUID) -> AlarmOccurrence:
        await self.find_by_id(alarm_id)
        occurrence = await self._occurrences.find_active_for_alarm(alarm_id)
        if occurrence is None:
            raise NoActiveOccurrenceError(alarm_id)
        return occurrence
