import asyncio
import threading
from io import BytesIO

import numpy as np
import sounddevice as sd
import soundfile as sf

from huerise.features.devices.application import AudioPlayer
from huerise.infrastructure.storage import StorageBackend

_SOUND_FOLDERS = {
    "wake-up-": "wake_up_sounds",
    "get-up-": "get_up_sounds",
}


class SoundDeviceAudioPlayer(AudioPlayer):
    def __init__(self, storage: StorageBackend) -> None:
        self._storage = storage
        self._volume = 100
        self._stop_event = threading.Event()
        self._playback_thread: threading.Thread | None = None

    async def play(self, audio_file: str, volume: int) -> None:
        await self.stop()
        self._volume = volume
        self._stop_event.clear()
        audio_data = await self._storage.download_bytes(self._storage_path(audio_file))
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self._play_blocking, audio_data)

    @staticmethod
    def _storage_path(audio_file: str) -> str:
        if "/" in audio_file:
            return audio_file
        for prefix, folder in _SOUND_FOLDERS.items():
            if audio_file.startswith(prefix):
                return f"{folder}/{audio_file}"
        return audio_file

    def _play_blocking(self, audio_data: bytes) -> None:
        data, samplerate = sf.read(BytesIO(audio_data), dtype="float32")
        chunk_size = 1024
        pos = 0

        def callback(outdata: np.ndarray, frames: int, time, status) -> None:
            nonlocal pos
            if self._stop_event.is_set():
                raise sd.CallbackStop
            chunk = data[pos : pos + frames]
            if len(chunk) < frames:
                outdata[: len(chunk)] = chunk * (self._volume / 100.0)
                outdata[len(chunk) :] = 0
                raise sd.CallbackStop
            outdata[:] = chunk * (self._volume / 100.0)
            pos += frames

        with sd.OutputStream(
            samplerate=samplerate,
            channels=data.shape[1] if data.ndim > 1 else 1,
            callback=callback,
        ) as stream:
            while stream.active and not self._stop_event.is_set():
                sd.sleep(chunk_size)

    async def stop(self) -> None:
        self._stop_event.set()
        if self._playback_thread and self._playback_thread.is_alive():
            await asyncio.get_running_loop().run_in_executor(
                None, self._playback_thread.join, 2.0
            )

    async def set_volume(self, volume: int) -> None:
        self._volume = volume
