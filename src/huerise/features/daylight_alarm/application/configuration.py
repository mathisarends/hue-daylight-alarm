from uuid import UUID

from huerise.configuration import (
    AfterAlarmConfig,
    DaylightAlarmConfig,
    NamedResourceConfig,
    YamlConfiguration,
)
from huerise.features.lighting.application import SceneNotFoundError, SceneService


class SceneDoesNotBelongToRoomError(Exception):
    pass


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
        after_alarm_brightness: int | None = None,
        after_alarm_delay_seconds: int | None = None,
    ) -> DaylightAlarmConfig:
        scenes = await self._scenes.list_scenes()
        scene = self._selected_scene(scenes, room_id, scene_id)
        after_alarm = None
        if after_alarm_scene_id is not None:
            assert after_alarm_room_id is not None
            assert after_alarm_brightness is not None
            assert after_alarm_delay_seconds is not None
            selected_after_alarm = self._selected_scene(
                scenes, after_alarm_room_id, after_alarm_scene_id
            )
            after_alarm = AfterAlarmConfig(
                room=NamedResourceConfig(
                    id=selected_after_alarm.room_id,
                    name=selected_after_alarm.room_name,
                ),
                scene=NamedResourceConfig(
                    id=selected_after_alarm.id,
                    name=selected_after_alarm.name,
                ),
                brightness=after_alarm_brightness,
                delay_seconds=after_alarm_delay_seconds,
            )
        alarm = DaylightAlarmConfig(
            room=NamedResourceConfig(id=scene.room_id, name=scene.room_name),
            scene=NamedResourceConfig(id=scene.id, name=scene.name),
            duration_seconds=duration_seconds,
            after_alarm=after_alarm,
        )
        self._configuration.save_daylight_alarm(alarm)
        return alarm

    @staticmethod
    def _selected_scene(scenes: list, room_id: UUID, scene_id: UUID):
        scene = next((item for item in scenes if item.id == scene_id), None)
        if scene is None:
            raise SceneNotFoundError(scene_id)
        if scene.room_id != room_id:
            raise SceneDoesNotBelongToRoomError()
        return scene
