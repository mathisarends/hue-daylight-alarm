import logging
from collections.abc import Iterable, Iterator

from huerise.features.alarm.domain import (
    Alarm,
    AlarmDefect,
    AlarmField,
    AlarmProfile,
    AlarmUnitOfWork,
    AlarmUnitOfWorkFactory,
    ProfileField,
    SunriseConfig,
)
from huerise.features.devices.application import LightEvents, Lights
from huerise.features.devices.domain import LightChange, LightResource, Room, Scene
from huerise.features.events.application import EventPublisher
from huerise.features.events.domain import (
    AlarmSnapshot,
    AlarmUpdated,
    HueriseEvent,
    ProfileSnapshot,
    ProfileUpdated,
)
from huerise.lifecycle import Runnable

logger = logging.getLogger(__name__)


class LightReferenceSync(Runnable):
    """Keeps the room and scene an alarm wakes up with in step with the bridge.

    An alarm stores a Hue room ID, a profile stores a scene ID, and both keep a
    copy of the name that resource had when it was picked. Renaming on the
    bridge makes the copy stale; deleting makes the ID unresolvable, which would
    otherwise only surface as a failed occurrence at 06:45. Both are handled
    here as the bridge reports them: names are refreshed, vanished resources are
    replaced where a sensible replacement exists, and what cannot be repaired is
    recorded on the alarm so a client can say so in advance.
    """

    def __init__(
        self,
        events: LightEvents,
        lights: Lights,
        unit_of_work_factory: AlarmUnitOfWorkFactory,
        publisher: EventPublisher,
    ) -> None:
        self._events = events
        self._lights = lights
        self._unit_of_work_factory = unit_of_work_factory
        self._publisher = publisher

    async def start(self) -> None:
        self._events.subscribe(self._on_change)

    async def stop(self) -> None:
        self._events.unsubscribe(self._on_change)

    async def _on_change(self, change: LightChange) -> None:
        # Published only once the transaction is through: a client must never be
        # told about a repair that then rolls back.
        published = (
            await self._sync_room(change)
            if change.resource is LightResource.ROOM
            else await self._sync_scene(change)
        )
        for event in published:
            self._publisher.publish(event)

    async def _sync_room(self, change: LightChange) -> list[HueriseEvent]:
        async with self._unit_of_work_factory.create() as uow:
            alarms = [
                alarm
                for alarm in await uow.alarms.find_all()
                if alarm.room_id == change.id
            ]
            if not alarms:
                return []

            if change.name is not None:
                repaired = [
                    (alarm, _rename_room(alarm, change.name)) for alarm in alarms
                ]
            else:
                # A bare identity is what a deletion looks like, but so is a change
                # to something we don't track -- only the bridge can tell them apart.
                rooms = await self._lights.list_rooms()
                if any(room.id == change.id for room in rooms):
                    return []

                logger.info(
                    "Hue room %s is gone, repairing what points at it", change.id
                )
                repaired = [(alarm, _repair_room(alarm, rooms)) for alarm in alarms]

            return [
                await self._save_alarm(uow, alarm, changed)
                for alarm, changed in repaired
                if changed
            ]

    async def _sync_scene(self, change: LightChange) -> list[HueriseEvent]:
        async with self._unit_of_work_factory.create() as uow:
            profiles = [
                profile
                for profile in await uow.profiles.find_all()
                if profile.sunrise_config.scene_id == change.id
            ]
            if not profiles:
                return []

            alarms = await uow.alarms.find_all()
            if change.name is not None:
                return await self._rename_scene(uow, profiles, alarms, change.name)

            rooms = await self._lights.list_rooms()
            if any(scene.id == change.id for scene in _scenes_of(rooms)):
                return []

            logger.info("Hue scene %s is gone, repairing what points at it", change.id)
            published: list[HueriseEvent] = []
            for profile in profiles:
                published.extend(await self._repair_scene(uow, profile, alarms, rooms))
            return published

    async def _rename_scene(
        self,
        uow: AlarmUnitOfWork,
        profiles: list[AlarmProfile],
        alarms: list[Alarm],
        name: str,
    ) -> list[HueriseEvent]:
        published: list[HueriseEvent] = []
        for profile in profiles:
            if profile.use_scene(profile.sunrise_config.scene_id, name):
                logger.info(
                    "Sunrise scene of profile %s is now called '%s'", profile.id, name
                )
                published.append(await self._save_profile(uow, profile))
            # The bridge just named the scene, so it is there again.
            published.extend(await self._flag_alarms(uow, profile, alarms, None))
        return published

    async def _repair_scene(
        self,
        uow: AlarmUnitOfWork,
        profile: AlarmProfile,
        alarms: list[Alarm],
        rooms: list[Room],
    ) -> list[HueriseEvent]:
        replacement = _replacement_scene(profile, alarms, rooms)
        if replacement is None:
            logger.warning(
                "Scene '%s' no longer exists and profile %s has no scene to fall "
                "back to",
                profile.sunrise_config.scene_name,
                profile.id,
            )
            return await self._flag_alarms(
                uow, profile, alarms, AlarmDefect.SCENE_MISSING
            )

        logger.info(
            "Profile %s wakes up with '%s' (%s) from now on, '%s' is gone",
            profile.id,
            replacement.name,
            replacement.id,
            profile.sunrise_config.scene_name,
        )
        profile.use_scene(replacement.id, replacement.name)
        return [
            await self._save_profile(uow, profile),
            *await self._flag_alarms(uow, profile, alarms, None),
        ]

    async def _flag_alarms(
        self,
        uow: AlarmUnitOfWork,
        profile: AlarmProfile,
        alarms: list[Alarm],
        defect: AlarmDefect | None,
    ) -> list[HueriseEvent]:
        """Carry a profile's scene trouble over to the alarms that run it.

        An alarm whose room is missing keeps that defect: the room explains the
        missing scene, and it is the one the user has to sort out.
        """
        running_it = [
            alarm
            for alarm in alarms
            if alarm.profile_id == profile.id
            and alarm.defect is not AlarmDefect.ROOM_MISSING
        ]
        return [
            await self._save_alarm(uow, alarm, [AlarmField.DEFECT])
            for alarm in running_it
            if alarm.set_defect(defect)
        ]

    async def _save_alarm(
        self, uow: AlarmUnitOfWork, alarm: Alarm, changed: list[AlarmField]
    ) -> HueriseEvent:
        saved = await uow.alarms.save(alarm)
        return AlarmUpdated(alarm=AlarmSnapshot.from_domain(saved), changed=changed)

    async def _save_profile(
        self, uow: AlarmUnitOfWork, profile: AlarmProfile
    ) -> HueriseEvent:
        saved = await uow.profiles.save(profile)
        return ProfileUpdated(
            profile=ProfileSnapshot.from_domain(saved),
            changed=[ProfileField.SUNRISE_SCENE],
        )


def _rename_room(alarm: Alarm, name: str) -> list[AlarmField]:
    changed = alarm.update(room_name=name)
    if changed:
        logger.info("Room of alarm %s is now called '%s'", alarm.id, name)
    return changed + _clear_missing_room(alarm)


def _repair_room(alarm: Alarm, rooms: list[Room]) -> list[AlarmField]:
    """Adopt the room that took over the name, or record the alarm as broken.

    A room deleted and set up again in the Hue app comes back under a new ID
    with the same name -- that is the one case worth repairing. Guessing any
    further would mean waking someone in a room they never chose.
    """
    replacement = _named(rooms, alarm.room_name)
    if replacement is None:
        logger.warning(
            "Room '%s' no longer exists, alarm %s cannot light anything",
            alarm.room_name,
            alarm.id,
        )
        if not alarm.set_defect(AlarmDefect.ROOM_MISSING):
            return []
        return [AlarmField.DEFECT]

    logger.info(
        "Room '%s' came back as %s, re-pointing alarm %s",
        replacement.name,
        replacement.id,
        alarm.id,
    )
    changed = alarm.update(room_id=replacement.id, room_name=replacement.name)
    return changed + _clear_missing_room(alarm)


def _clear_missing_room(alarm: Alarm) -> list[AlarmField]:
    """The bridge just reported the room, so a ROOM_MISSING defect is stale."""
    if alarm.defect is not AlarmDefect.ROOM_MISSING:
        return []
    alarm.set_defect(None)
    return [AlarmField.DEFECT]


def _replacement_scene(
    profile: AlarmProfile, alarms: list[Alarm], rooms: list[Room]
) -> Scene | None:
    """The closest thing to the scene that vanished.

    A scene deleted and rebuilt in the Hue app keeps its name, so a namesake is
    the best guess -- preferably in a room this profile actually wakes up.
    Failing that, any scene of those rooms still lights them, so the brightest
    one the sunrise can ramp towards beats no sunrise at all.
    """
    sunrise = profile.sunrise_config
    room_ids = {alarm.room_id for alarm in alarms if alarm.profile_id == profile.id}
    own_rooms = [room for room in rooms if room.id in room_ids]

    for candidates in (own_rooms, rooms):
        namesake = _named(_scenes_of(candidates), sunrise.scene_name)
        if namesake is not None:
            return namesake

    reachable = [
        scene
        for scene in _scenes_of(own_rooms)
        if _sunrise_target(scene, sunrise) > sunrise.brightness_start
    ]
    return max(
        reachable, key=lambda scene: _sunrise_target(scene, sunrise), default=None
    )


def _sunrise_target(scene: Scene, sunrise: SunriseConfig) -> int:
    """The brightness the runner would ramp this scene to, capped as it caps it."""
    if scene.brightness is None:
        return sunrise.brightness_end
    return min(round(scene.brightness), sunrise.brightness_end)


def _scenes_of(rooms: Iterable[Room]) -> Iterator[Scene]:
    return (scene for room in rooms for scene in room.scenes)


def _named[T: Room | Scene](candidates: Iterable[T], name: str) -> T | None:
    wanted = name.casefold()
    return next(
        (candidate for candidate in candidates if candidate.name.casefold() == wanted),
        None,
    )
