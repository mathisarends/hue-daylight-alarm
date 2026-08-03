from abc import ABC, abstractmethod


class Lights(ABC):
    @abstractmethod
    async def activate_scene(self, room_name: str, scene_name: str) -> None: ...

    @abstractmethod
    async def set_brightness(self, room_name: str, brightness: int) -> None: ...
