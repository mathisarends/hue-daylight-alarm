import asyncio
from pathlib import Path
import soco
from hypercorn.asyncio import serve
from hypercorn.config import Config as HypercornConfig
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

from backend.src.domain.value_objects import AudioFile
from backend.src.infrastructure.audio.ports import AudioPlayerStrategy
from backend.src.shared.logging import LoggingMixin


class SonosStrategy(AudioPlayerStrategy, LoggingMixin):
    def __init__(
        self,
        sounds_directory: Path,
        speaker_ip: str = "192.168.178.68",
        server_port: int = 8000,
    ):
        super().__init__(sounds_directory)
        self.speaker = soco.SoCo(speaker_ip)
        self.server_port = server_port
        self.server_ip = self._get_server_ip()

        self._server_task: asyncio.Task | None = None
        self._shutdown_trigger = asyncio.Event()
        self._app = self._create_app()

    def _get_server_ip(self) -> str:
        import socket

        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return socket.gethostbyname(socket.gethostname())

    def _create_app(self) -> FastAPI:
        app = FastAPI(
            title="Sonos Audio Server", version="1.0.0", docs_url=None, redoc_url=None
        )

        @app.get("/sounds/{path:path}")
        async def serve_sound(path: str):
            file_path = self._sounds_directory / path

            if not file_path.exists():
                raise HTTPException(status_code=404, detail="Sound not found")

            return FileResponse(
                file_path,
                media_type="audio/mpeg",
                headers={
                    "Cache-Control": "public, max-age=3600",
                    "Accept-Ranges": "bytes",
                },
            )

        return app

    async def initialize(self) -> None:
        if self._server_task is not None:
            return

        config = HypercornConfig()
        config.bind = [f"0.0.0.0:{self.server_port}"]
        config.accesslog = None
        config.errorlog = None

        self.logger.info(
            f"Starting audio server at http://{self.server_ip}:{self.server_port} "
            f"(serving: {self._sounds_directory})"
        )

        self._server_task = asyncio.create_task(
            serve(self._app, config, shutdown_trigger=self._shutdown_trigger.wait)
        )

    async def cleanup(self) -> None:
        if self._server_task is None:
            return

        self.logger.info("Stopping audio server...")

        self._shutdown_trigger.set()

        try:
            await asyncio.wait_for(self._server_task, timeout=5.0)
        except asyncio.TimeoutError:
            self.logger.warning("Server shutdown timeout, forcing cancellation")
            self._server_task.cancel()
            try:
                await self._server_task
            except asyncio.CancelledError:
                pass

        self._server_task = None
        self._shutdown_trigger.clear()

    def _build_url(self, audio_file: AudioFile) -> str:
        relative_path = audio_file.path.relative_to(self._sounds_directory)
        return f"http://{self.server_ip}:{self.server_port}/sounds/{relative_path}"

    async def play(self, audio_file: AudioFile) -> None:
        url = self._build_url(audio_file)
        self.logger.info(f"Playing: {url}")
        self.speaker.play_uri(url)

    async def stop(self) -> None:
        self.speaker.stop()

    async def set_volume(self, volume: int) -> None:
        self.speaker.volume = volume
