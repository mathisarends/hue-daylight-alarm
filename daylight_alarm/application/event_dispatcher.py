from daylight_alarm.domain.events import DomainEvent
from daylight_alarm.infrastructure.event_handlers import EventHandler


class EventDispatcher:
    def __init__(self, handlers: list[EventHandler]):
        self._handlers = handlers

    async def dispatch(self, event: DomainEvent) -> None:
        for handler in self._handlers:
            if handler.can_handle(event):
                await handler.handle(event)

    async def dispatch_all(self, events: list[DomainEvent]) -> None:
        for event in events:
            await self.dispatch(event)
