import logging

from huerise.features.devices.application.ports import LightEvents
from huerise.features.devices.domain import LightChange

logger = logging.getLogger(__name__)


class LightChangeLogger:
    """Reports bridge changes while nothing else acts on them yet.

    This is the seam the profile and alarm sync will hang off: the alarms
    store a scene name and a room name of their own, and both go stale the
    moment somebody renames one in the Hue app.
    """

    def __init__(self, events: LightEvents) -> None:
        self._events = events

        self._events.subscribe(self._log)

    async def _log(self, change: LightChange) -> None:
        logger.info(
            "Hue %s %s changed, name=%s", change.resource, change.id, change.name
        )
