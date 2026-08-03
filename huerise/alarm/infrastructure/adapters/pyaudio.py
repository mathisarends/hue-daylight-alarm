import asyncio
import threading

import numpy as np
import sounddevice as sd
import soundfile as sf

from huerise.alarm.application import AudioPlayer


class SoundDeviceAudioPlayer(AudioPlayer):
    def __init__(self) -> None:
        self._volume = 100
        self._stop_event = threading.Event()
        self._playback_thread: threading.Thread | None = None

    async def play(self, audio_file: str, volume: int) -> None:
        await self.stop()
        self._volume = volume
        self._stop_event.clear()
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self._play_blocking, audio_file)

    def _play_blocking(self, audio_file: str) -> None:
        data, samplerate = sf.read(audio_file, dtype="float32")
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
        ):
            while not self._stop_event.is_set():
                sd.sleep(chunk_size)

    async def stop(self) -> None:
        self._stop_event.set()
        if self._playback_thread and self._playback_thread.is_alive():
            await asyncio.get_running_loop().run_in_executor(
                None, self._playback_thread.join, 2.0
            )

    async def set_volume(self, volume: int) -> None:
        self._volume = volume
