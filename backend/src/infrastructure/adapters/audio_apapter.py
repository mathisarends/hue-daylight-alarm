import asyncio
from backend.src.domain.value_objects import AudioFile
from backend.src.infrastructure.ports import AudioService
import pygame


class PygameAudioService(AudioService):
    def __init__(self):
        pygame.mixer.init()

    async def play(self, audio_file: AudioFile) -> None:
        sound = pygame.mixer.Sound(str(audio_file.path))
        sound.play()

        while pygame.mixer.get_busy():
            await asyncio.sleep(0.1)

    async def stop(self) -> None:
        pygame.mixer.stop()
