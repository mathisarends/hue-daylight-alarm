import asyncio
import logging
from collections.abc import Awaitable, Callable
from contextlib import suppress
from typing import Protocol
from uuid import UUID

from huerise.configuration import DaylightAlarmConfig, HueriseConfig
from huerise.features.lighting.hue import (
    HueClient,
    HueClientFactory,
    HueCredentials,
    HueUnavailableError,
    RoomNotFoundError,
    SceneNotFoundError,
    room_for_scene,
)

logger = logging.getLogger(__name__)

type Sleep = Callable[[float], Awaitable[None]]


class ConfigurationSource(Protocol):
    def load(self) -> HueriseConfig: ...


class CredentialsSource(Protocol):
    def get(self) -> HueCredentials: ...


class AlarmAlreadyRunningError(Exception):
    pass


class DaylightAlarm:
    def __init__(
        self,
        configuration: ConfigurationSource,
        credentials: CredentialsSource,
        clients: HueClientFactory,
        *,
        step_interval: float = 1.0,
        sleep: Sleep = asyncio.sleep,
    ) -> None:
        self._configuration = configuration
        self._credentials = credentials
        self._clients = clients
        self._step_interval = step_interval
        self._sleep = sleep
        self._task: asyncio.Task[None] | None = None
        self._lock = asyncio.Lock()

    @property
    def is_running(self) -> bool:
        return self._task is not None and not self._task.done()

    async def start(self) -> None:
        await self._start(self._configuration.load().daylight_alarm)

    async def demo(self, room_id: UUID, scene_id: UUID) -> None:
        configured = self._configuration.load().daylight_alarm
        demo = configured.model_copy(
            update={"scene_id": scene_id, "duration_seconds": 10}
        )
        await self._start(demo, room_id=room_id)

    async def _start(
        self, config: DaylightAlarmConfig, *, room_id: UUID | None = None
    ) -> None:
        async with self._lock:
            if self.is_running:
                raise AlarmAlreadyRunningError("Daylight alarm is already running")

            try:
                client = self._clients.create(self._credentials.get())
            except HueUnavailableError:
                raise
            except Exception as error:
                raise HueUnavailableError(
                    "Could not initialize Hue Bridge connection"
                ) from error
            try:
                room = room_for_scene(
                    await client.list_rooms(), config.scene_id, room_id=room_id
                )
                await client.activate_scene(
                    config.scene_id, brightness=config.start_brightness
                )
            except Exception as error:
                await self._close(client)
                if isinstance(error, HueUnavailableError):
                    raise
                if isinstance(error, SceneNotFoundError | RoomNotFoundError):
                    raise
                raise HueUnavailableError(
                    "Could not communicate with Hue Bridge"
                ) from error

            task = asyncio.create_task(self._run(client, room.id, config))
            self._task = task
            task.add_done_callback(self._finished)

    async def stop(self) -> None:
        async with self._lock:
            task, self._task = self._task, None
            if task is None or task.done():
                return
            task.cancel()

        with suppress(asyncio.CancelledError):
            await task

    async def _run(
        self, client: HueClient, room_id: UUID, config: DaylightAlarmConfig
    ) -> None:
        elapsed = 0.0
        try:
            while elapsed < config.duration_seconds:
                delay = min(self._step_interval, config.duration_seconds - elapsed)
                await self._sleep(delay)
                elapsed += delay
                progress = elapsed / config.duration_seconds
                brightness = (
                    config.start_brightness
                    + (config.end_brightness - config.start_brightness) * progress
                )
                await client.set_brightness(room_id, brightness)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Daylight alarm failed during execution")
        finally:
            await self._close(client)

    def _finished(self, task: asyncio.Task[None]) -> None:
        if self._task is task:
            self._task = None
        if not task.cancelled():
            task.exception()

    @staticmethod
    async def _close(client: HueClient) -> None:
        try:
            await client.close()
        except Exception:
            logger.warning("Could not close Hue client", exc_info=True)
