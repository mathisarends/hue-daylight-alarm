from abc import ABC, abstractmethod


class AudioPlayer(ABC):
    @abstractmethod
    async def play(self, audio_file: str, volume: int) -> None: ...

    @abstractmethod
    async def stop(self) -> None: ...

    @abstractmethod
    async def set_volume(self, volume: int) -> None: ...
