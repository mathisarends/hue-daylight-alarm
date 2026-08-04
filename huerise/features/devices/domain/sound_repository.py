from abc import ABC, abstractmethod
from uuid import UUID

from .exceptions import SoundNotFoundError
from .sound import Sound, SoundCategory


class SoundRepository(ABC):
    @abstractmethod
    async def find_by_id(self, sound_id: UUID) -> Sound | None: ...

    @abstractmethod
    async def find_all(self, category: SoundCategory | None = None) -> list[Sound]: ...

    @abstractmethod
    async def save(self, sound: Sound) -> Sound: ...

    async def get(self, sound_id: UUID) -> Sound:
        sound = await self.find_by_id(sound_id)
        if sound is None:
            raise SoundNotFoundError(sound_id)
        return sound
