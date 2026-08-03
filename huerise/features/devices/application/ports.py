from abc import ABC, abstractmethod


class AudioPlayer(ABC):
    @abstractmethod
    async def play(self, sound_id: str, volume: int) -> None: ...

    @abstractmethod
    async def stop(self) -> None: ...

    @abstractmethod
    async def set_volume(self, volume: int) -> None: ...


class Lights(ABC):
    @abstractmethod
    async def activate_scene(self, room_name: str, scene_name: str) -> None: ...

    @abstractmethod
    async def set_brightness(self, room_name: str, brightness: int) -> None: ...
