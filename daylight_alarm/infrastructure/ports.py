from abc import ABC, abstractmethod
from daylight_alarm.domain.value_objects import AudioFile


class AudioService(ABC):
    @abstractmethod
    async def play(self, audio_file: AudioFile) -> None:
        pass

    @abstractmethod
    async def stop(self) -> None:
        pass
