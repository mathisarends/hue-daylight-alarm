from pathlib import Path

from backend.src.infrastructure.audio.ports import AudioPlayerStrategy
from backend.src.infrastructure.audio.strategies import PygameStrategy
from backend.src.shared.logging import LoggingMixin


class AudioPlayer(LoggingMixin):
    def __init__(
        self,
        sounds_directory: Path,
        default_strategy: AudioPlayerStrategy | None = None,
    ):
        self._sounds_directory = sounds_directory
        self._current_strategy: AudioPlayerStrategy = (
            default_strategy or PygameStrategy(sounds_directory)
        )

    @property
    def current_strategy(self) -> str:
        return self._current_strategy.__class__.__name__

    async def play(self, relative_path: str, volume: int = 25) -> None:
        if not self._current_strategy:
            raise RuntimeError("No strategy initialized")

        audio_file = self._current_strategy._resolve_audio_file(relative_path)
        await self._current_strategy.set_volume(volume)
        await self._current_strategy.play(audio_file)

    async def stop(self) -> None:
        if self._current_strategy:
            await self._current_strategy.stop()

    async def set_volume(self, volume: int) -> None:
        if self._current_strategy:
            await self._current_strategy.set_volume(volume)

    async def switch_strategy(self, strategy: AudioPlayerStrategy) -> None:
        new_strategy_name = strategy.__class__.__name__

        if new_strategy_name == self.current_strategy:
            self.logger.debug(f"Already using {new_strategy_name} strategy")
            return

        self.logger.info(
            f"Switching from {self.current_strategy} to {new_strategy_name}"
        )

        await self._current_strategy.cleanup()

        self._current_strategy = strategy
        await self._current_strategy.initialize()

        self.logger.info(f"Successfully switched to {new_strategy_name}")

    async def __aenter__(self):
        await self._current_strategy.initialize()
        self.logger.debug(f"Initialized {self.current_strategy} strategy")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._current_strategy.cleanup()
        self.logger.debug(f"Cleaned up {self.current_strategy} strategy")
