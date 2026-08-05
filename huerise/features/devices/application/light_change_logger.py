import logging

from huerise.features.devices.application.ports import LightEvents
from huerise.features.devices.domain import LightChange
from huerise.lifecycle import Runnable

logger = logging.getLogger(__name__)


class LightChangeLogger(Runnable):
    """Reports bridge changes while nothing else acts on them yet."""

    def __init__(self, events: LightEvents) -> None:
        self._events = events

    async def start(self) -> None:
        self._events.subscribe(self._log)

    async def stop(self) -> None:
        self._events.unsubscribe(self._log)

    async def _log(self, change: LightChange) -> None:
        logger.info(
            "Hue %s %s changed, name=%s", change.resource, change.id, change.name
        )
