from hueify import Room
from backend.src.domain.value_objects import Brightness


class HueifyRoomService:
    async def activate_scene(self, room_name: str, scene_name: str) -> None:
        room = await Room.from_name(room_name)
        await room.activate_scene(scene_name)

    async def set_brightness(self, room_name: str, brightness: Brightness) -> None:
        room = await Room.from_name(room_name)
        await room.set_brightness_percentage(brightness.percentage)
