import asyncio
import pygame
from pathlib import Path
from backend.src.domain.value_objects import AudioFile
from backend.src.infrastructure.audio.ports import AudioPlayerStrategy


class PygameStrategy(AudioPlayerStrategy):
    def __init__(self, sounds_directory: Path):
        super().__init__(sounds_directory)
        pygame.mixer.init()
        self._current_sound: pygame.mixer.Sound | None = None

    async def play(self, audio_file: AudioFile) -> None:
        self._current_sound = pygame.mixer.Sound(str(audio_file.path))
        self._current_sound.play()

        while pygame.mixer.get_busy():
            await asyncio.sleep(0.1)

    async def stop(self) -> None:
        pygame.mixer.stop()
        self._current_sound = None

    async def set_volume(self, volume: int) -> None:
        pygame.mixer.music.set_volume(volume / 100.0)
