from uuid import UUID

from huerise.configuration import (
    AfterAlarmConfig,
    DaylightAlarmConfig,
    NamedResourceConfig,
    YamlConfiguration,
)
from huerise.features.lighting.application import (
    Room,
    Scene,
    SceneService,
    room_for_scene,
)


class SceneDoesNotBelongToRoomError(Exception):
    def __init__(self, scene_id: UUID, room_id: UUID) -> None:
        super().__init__(f"Hue scene {scene_id} does not belong to room {room_id}")
        self.scene_id = scene_id
        self.room_id = room_id


class DaylightAlarmConfiguration:
    def __init__(
        self,
        configuration: YamlConfiguration,
        scenes: SceneService,
    ) -> None:
        self._configuration = configuration
        self._scenes = scenes

    def get(self) -> DaylightAlarmConfig:
        return self._configuration.load().daylight_alarm

    async def save(
        self,
        *,
        room_id: UUID,
        scene_id: UUID,
        duration_seconds: int,
        after_alarm_room_id: UUID | None = None,
        after_alarm_scene_id: UUID | None = None,
        after_alarm_delay_seconds: int | None = None,
    ) -> DaylightAlarmConfig:
        rooms = await self._scenes.list_rooms()
        room, scene = _selected_scene(rooms, room_id, scene_id)
        after_alarm = None
        if after_alarm_scene_id is not None:
            assert after_alarm_room_id is not None
            assert after_alarm_delay_seconds is not None
            after_alarm_room, after_alarm_scene = _selected_scene(
                rooms, after_alarm_room_id, after_alarm_scene_id
            )
            after_alarm = AfterAlarmConfig(
                room=NamedResourceConfig(
                    id=after_alarm_room.id, name=after_alarm_room.name
                ),
                scene=NamedResourceConfig(
                    id=after_alarm_scene.id, name=after_alarm_scene.name
                ),
                delay_seconds=after_alarm_delay_seconds,
            )
        alarm = DaylightAlarmConfig(
            room=NamedResourceConfig(id=room.id, name=room.name),
            scene=NamedResourceConfig(id=scene.id, name=scene.name),
            duration_seconds=duration_seconds,
            after_alarm=after_alarm,
        )
        self._configuration.save_daylight_alarm(alarm)
        return alarm


def _selected_scene(
    rooms: list[Room], room_id: UUID, scene_id: UUID
) -> tuple[Room, Scene]:
    room = room_for_scene(rooms, scene_id)
    if room.id != room_id:
        raise SceneDoesNotBelongToRoomError(scene_id, room_id)
    scene = next(scene for scene in room.scenes if scene.id == scene_id)
    return room, scene
