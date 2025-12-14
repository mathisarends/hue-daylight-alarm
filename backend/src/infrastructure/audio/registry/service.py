from pathlib import Path

from backend.src.infrastructure.audio.registry.models import RegisteredSound
from backend.src.shared.logging import LoggingMixin


class AudioRegistry(LoggingMixin):
    def __init__(self, sounds_directory: Path):
        self._sounds_directory = sounds_directory
        self._sounds: list[RegisteredSound] = []
        self._scan_sounds()

    def _scan_sounds(self) -> None:
        if not self._sounds_directory.exists():
            self.logger.warning(f"Sounds directory not found: {self._sounds_directory}")
            return

        supported_extensions = {".mp3", ".wav", ".ogg", ".flac", ".m4a"}

        for file_path in self._sounds_directory.rglob("*"):
            if file_path.suffix.lower() in supported_extensions:
                self._register_sound(file_path)

        self.logger.info(f"Registered {len(self._sounds)} sound(s)")

    def _register_sound(self, file_path: Path) -> None:
        relative_path = file_path.relative_to(self._sounds_directory)
        name = file_path.stem
        category = self._extract_category(file_path)

        sound = RegisteredSound(
            name=name,
            relative_path=relative_path.as_posix(),
            category=category,
        )

        self._sounds.append(sound)

    def _extract_category(self, file_path: Path) -> str | None:
        parent = file_path.parent.name
        if parent != self._sounds_directory.name:
            return parent
        return None

    def get_all(self) -> list[RegisteredSound]:
        return self._sounds

    def get_by_category(self, category: str) -> list[RegisteredSound]:
        return [sound for sound in self._sounds if sound.category == category]

    def get_wake_up_sounds(self) -> list[RegisteredSound]:
        return self.get_by_category("wake_up_sounds")

    def get_get_up_sounds(self) -> list[RegisteredSound]:
        return self.get_by_category("get_up_sounds")
