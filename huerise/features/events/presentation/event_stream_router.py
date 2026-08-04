from collections.abc import AsyncIterator
from typing import Annotated, Any

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Depends, Header
from fastapi.responses import StreamingResponse
from pydantic import TypeAdapter

from huerise.features.events.application import EventStreamHub
from huerise.features.events.domain import AnyHueriseEvent
from huerise.features.events.presentation.sse import frames
from huerise.presentation import require_access_token

event_stream_router = APIRouter(
    tags=["Events"],
    route_class=DishkaRoute,
    dependencies=[Depends(require_access_token)],
)

_STREAM_HEADERS = {
    "Cache-Control": "no-cache",
    # Tells nginx not to buffer, which would hold frames back until the
    # connection closes.
    "X-Accel-Buffering": "no",
}

_DESCRIPTION = """
Server-sent events covering every change to alarms and to the run currently in
progress, so a display can stay in sync without polling.

Each frame carries the event id in `id:`, the discriminator in `event:` and the
event itself as JSON in `data:`. Reconnect with `Last-Event-ID` to resume; if
that id has rolled out of the buffer nothing is replayed, so resync over
`GET /alarms` first. A `: keepalive` comment arrives whenever the stream is
idle.
"""


def _frame_schema() -> dict[str, Any]:
    """The union as OpenAPI sees it.

    FastAPI documents any non-JSON response as a bare string, so the
    discriminator is attached by hand. `response_model` still registers the
    member schemas under `components`, which is what these refs point at.
    """
    schema = TypeAdapter(AnyHueriseEvent).json_schema(
        ref_template="#/components/schemas/{model}", mode="serialization"
    )
    schema.pop("$defs", None)
    return schema


class EventStreamResponse(StreamingResponse):
    media_type = "text/event-stream"


@event_stream_router.get(
    "/eventstream",
    operation_id="streamEvents",
    summary="Subscribe to the alarm event stream",
    description=_DESCRIPTION,
    response_class=EventStreamResponse,
    response_model=AnyHueriseEvent,
    responses={200: {"content": {"text/event-stream": {"schema": _frame_schema()}}}},
)
async def stream_events(
    hub: FromDishka[EventStreamHub],
    last_event_id: Annotated[str | None, Header(alias="Last-Event-ID")] = None,
) -> EventStreamResponse:
    async def stream() -> AsyncIterator[str]:
        async with hub.subscribe(last_event_id) as events:
            async for frame in frames(events):
                yield frame

    return EventStreamResponse(stream(), headers=_STREAM_HEADERS)
