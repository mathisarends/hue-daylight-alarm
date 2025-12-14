from abc import ABC, abstractmethod
from pathlib import Path
from backend.src.domain.value_objects import AudioFile


class AudioPlayerStrategy(ABC):
    def __init__(self, sounds_directory: Path):
        self._sounds_directory = sounds_directory

    @abstractmethod
    async def play(self, audio_file: AudioFile) -> None:
        pass

    @abstractmethod
    async def stop(self) -> None:
        pass

    @abstractmethod
    async def set_volume(self, volume: int) -> None:
        pass

    async def initialize(self) -> None:
        pass

    async def cleanup(self) -> None:
        pass

    def _resolve_audio_file(self, relative_path: str) -> AudioFile:
        full_path = self._sounds_directory / relative_path
        if not full_path.exists():
            raise FileNotFoundError(f"Audio file not found: {full_path}")
        return AudioFile(path=full_path)
