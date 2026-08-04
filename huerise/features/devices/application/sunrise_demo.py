import asyncio
import logging
from contextlib import suppress
from datetime import timedelta
from uuid import UUID

from huerise.features.devices.application.ports import Lights
from huerise.features.devices.domain import SunriseRamp, SunriseStep, sunrise_steps

logger = logging.getLogger(__name__)

# A demo is watched, not slept through, so the same climb is compressed into
# seconds. One second is as often as the bridge accepts room-wide changes.
DEMO_DURATION = timedelta(seconds=20)
DEMO_STEP_INTERVAL = timedelta(seconds=1)


class SunriseDemoRunner:
    """Replays a sunrise ramp on the real lights, fast.

    Held for the lifetime of the app, not the request: the ramp keeps running
    after the caller is answered, and only one may run at a time -- two would
    fight over the same lights.
    """

    def __init__(
        self, lights: Lights, step_interval: timedelta = DEMO_STEP_INTERVAL
    ) -> None:
        self._lights = lights
        self._step_interval = step_interval
        self._running: asyncio.Task[None] | None = None

    @property
    def step_interval(self) -> timedelta:
        return self._step_interval

    async def start(self, room_id: UUID, scene_id: UUID, ramp: SunriseRamp) -> int:
        """Begin the ramp in the background, replacing any demo already running.

        Returns the number of brightness steps it will take, so the caller can
        describe the run it just started. The scene is activated before the
        task is spawned, letting a bridge failure surface to the caller.
        """
        await self.stop()
        steps = list(sunrise_steps(ramp, self._step_interval))

        await self._lights.activate_scene(scene_id, brightness=ramp.brightness_start)
        self._running = asyncio.create_task(self._replay(room_id, steps))
        return len(steps)

    async def stop(self) -> None:
        """Cancel the running demo, leaving the lights wherever it got to."""
        task, self._running = self._running, None
        if task is None or task.done():
            return

        task.cancel()
        with suppress(asyncio.CancelledError):
            await task

    async def _replay(self, room_id: UUID, steps: list[SunriseStep]) -> None:
        try:
            for step in steps:
                await self._lights.set_brightness(room_id, step.brightness)
                await asyncio.sleep(self._step_interval.total_seconds())
        except asyncio.CancelledError:
            logger.info("Sunrise demo in room %s was stopped", room_id)
            raise
        except Exception:
            logger.exception("Sunrise demo in room %s failed", room_id)
