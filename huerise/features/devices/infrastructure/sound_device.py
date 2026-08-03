import asyncio
import threading
from io import BytesIO

import numpy as np
import sounddevice as sd
import soundfile as sf

from huerise.features.devices.application import AudioPlayer, SoundCatalog
from huerise.infrastructure.storage import StorageBackend

_CHUNK_SIZE = 1024


class SoundDeviceAudioPlayer(AudioPlayer):
    def __init__(self, catalog: SoundCatalog, storage: StorageBackend) -> None:
        self._catalog = catalog
        self._storage = storage
        self._volume = 100
        self._stop_event = threading.Event()

    async def play(self, sound_id: str, volume: int) -> None:
        await self.stop()
        self._volume = volume
        self._stop_event.clear()

        sound = await self._catalog.get(sound_id)
        audio_data = await self._storage.download_bytes(sound.storage_path)

        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self._play_blocking, audio_data)

    def _play_blocking(self, audio_data: bytes) -> None:
        data, samplerate = sf.read(BytesIO(audio_data), dtype="float32")
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
                sd.sleep(_CHUNK_SIZE)

    async def stop(self) -> None:
        self._stop_event.set()

    async def set_volume(self, volume: int) -> None:
        self._volume = volume
