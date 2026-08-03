import asyncio
import logging
from abc import ABC, abstractmethod
from collections.abc import Sequence
from datetime import datetime, timezone
from uuid import UUID, uuid4

from huerise.domain import Alarm, AlarmNotFoundError, AlarmRepository, Weekday
from huerise.domain.views import Schedule

logger = logging.getLogger(__name__)


# --- Ports -------------------------------------------------------------


class Lights(ABC):
    @abstractmethod
    async def activate_scene(self, room_name: str, scene_name: str) -> None: ...

    @abstractmethod
    async def set_brightness(self, room_name: str, brightness: int) -> None: ...


class AudioPlayer(ABC):
    @abstractmethod
    async def play(self, audio_file: str, volume: int) -> None: ...

    @abstractmethod
    async def stop(self) -> None: ...

    @abstractmethod
    async def set_volume(self, volume: int) -> None: ...


# --- Service -------------------------------------------------------------


class AlarmService:
    def __init__(self, alarm_repository: AlarmRepository, audio: AudioPlayer) -> None:
        self._alarm_repository = alarm_repository
        self._audio = audio

    async def list_alarms(self) -> Sequence[Alarm]:
        return await self._alarm_repository.get_all()

    async def create_one_time(
        self,
        label: str,
        hour: int,
        minute: int,
        room_name: str,
        intro_audio_file: str = "wake-up-bowls.mp3",
        ringtone_audio_file: str = "get-up-aurora.mp3",
    ) -> Alarm:
        logger.info("Creating one-time alarm '%s' at %02d:%02d", label, hour, minute)
        alarm = Alarm.create_one_time(
            label=label,
            hour=hour,
            minute=minute,
            room_name=room_name,
            intro_audio_file=intro_audio_file,
            ringtone_audio_file=ringtone_audio_file,
        )
        return await self._alarm_repository.save(alarm)

    async def create_recurring(
        self,
        label: str,
        hour: int,
        minute: int,
        days: frozenset[Weekday],
        room_name: str,
        intro_audio_file: str = "wake-up-bowls.mp3",
        ringtone_audio_file: str = "get-up-aurora.mp3",
    ) -> Alarm:
        logger.info("Creating recurring alarm '%s' at %02d:%02d", label, hour, minute)
        alarm = Alarm.create_recurring(
            label=label,
            hour=hour,
            minute=minute,
            days=set(days),
            series_id=uuid4(),
            room_name=room_name,
            intro_audio_file=intro_audio_file,
            ringtone_audio_file=ringtone_audio_file,
        )
        return await self._alarm_repository.save(alarm)

    async def activate(self, alarm_id: UUID) -> Alarm:
        logger.info("Activating alarm %s", alarm_id)
        alarm = await self._get_or_raise(alarm_id)
        alarm.activate()
        return await self._alarm_repository.save(alarm)

    async def deactivate(self, alarm_id: UUID) -> Alarm:
        logger.info("Deactivating alarm %s", alarm_id)
        alarm = await self._get_or_raise(alarm_id)
        alarm.deactivate()
        return await self._alarm_repository.save(alarm)

    async def cancel(self, alarm_id: UUID) -> Alarm:
        logger.info("Cancelling alarm %s", alarm_id)
        alarm = await self._get_or_raise(alarm_id)
        alarm.cancel()
        return await self._alarm_repository.save(alarm)

    async def snooze(self, alarm_id: UUID, minutes: int = 10) -> Alarm:
        logger.info("Snoozing alarm %s for %d minutes", alarm_id, minutes)
        alarm = await self._get_or_raise(alarm_id)
        alarm.snooze(minutes)
        await self._audio.stop()
        return await self._alarm_repository.save(alarm)

    async def delete(self, alarm_id: UUID) -> None:
        logger.info("Deleting alarm %s", alarm_id)
        await self._get_or_raise(alarm_id)
        await self._alarm_repository.delete(alarm_id)

    async def delete_series(self, series_id: UUID) -> None:
        logger.info("Deleting alarm series %s", series_id)
        alarms = await self._alarm_repository.get_all()
        series_alarms = [a for a in alarms if a.series_id == series_id]
        for alarm in series_alarms:
            await self._alarm_repository.delete(alarm.id)

    async def set_volume(self, volume: int) -> None:
        logger.info("Setting volume to %d", volume)
        await self._audio.set_volume(volume)

    async def _get_or_raise(self, alarm_id: UUID) -> Alarm:
        alarm = await self._alarm_repository.get(alarm_id)
        if alarm is None:
            raise AlarmNotFoundError(alarm_id)
        return alarm


# --- Scheduler ---------------------------------------------------------


class AlarmRunner:
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


class AlarmScheduler:
    def __init__(self, repo: AlarmRepository, runner: AlarmRunner) -> None:
        self._repo = repo
        self._runner = runner

    async def run(self) -> None:
        while True:
            await self._tick()
            await asyncio.sleep(30)

    async def _tick(self) -> None:
        now = datetime.now(timezone.utc)
        try:
            alarms = await self._repo.get_scheduled()
        except Exception:
            logger.exception("Error fetching scheduled alarms")
            return

        for alarm in alarms:
            if self._should_trigger(alarm.schedule, now):
                asyncio.create_task(self._runner.run(alarm))

    @staticmethod
    def _should_trigger(schedule: Schedule, now: datetime) -> bool:
        if schedule.hour != now.hour or schedule.minute != now.minute:
            return False
        if schedule.recurrence is None:
            return True
        return Weekday(now.weekday()) in schedule.recurrence
