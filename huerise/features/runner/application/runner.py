import asyncio
import logging

from huerise.features.alarm.domain import Alarm, AlarmRepository
from huerise.features.alarm.application.ports import AudioPlayer
from huerise.features.runner.application.ports import Lights
from huerise.features.runner.application.runner_port import (
    AlarmRunner as AlarmRunnerPort,
)

logger = logging.getLogger(__name__)


class AlarmRunner(AlarmRunnerPort):
    def __init__(
        self,
        lights: Lights,
        audio: AudioPlayer,
        repo: AlarmRepository,
    ) -> None:
        self._lights = lights
        self._audio = audio
        self._repo = repo

    async def run(self, alarm: Alarm) -> None:
        try:
            alarm.trigger()
            await self._repo.save(alarm)
            await self._run_sunrise(alarm)

            alarm.ring()
            await self._repo.save(alarm)
            await self._run_ringtone(alarm)

            alarm.complete()
            await self._repo.save(alarm)
        except Exception:
            logger.exception("Alarm %s failed during execution", alarm.id)

    async def _run_sunrise(self, alarm: Alarm) -> None:
        cfg = alarm.sunrise_config
        intro_cfg = alarm.intro_config

        asyncio.create_task(self._audio.play(intro_cfg.audio_file, volume=50))
        await self._lights.activate_scene(cfg.room_name, cfg.scene_name)

        for step in range(cfg.steps):
            brightness = cfg.brightness_start + int(
                (cfg.brightness_end - cfg.brightness_start)
                * step
                / max(cfg.steps - 1, 1)
            )
            await self._lights.set_brightness(cfg.room_name, brightness)
            await asyncio.sleep(cfg.step_interval_seconds)

    async def _run_ringtone(self, alarm: Alarm) -> None:
        cfg = alarm.ringtone_config
        await self._audio.stop()
        await self._audio.play(cfg.audio_file, cfg.volume)
