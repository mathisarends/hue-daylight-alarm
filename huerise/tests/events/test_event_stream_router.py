from collections.abc import AsyncGenerator, AsyncIterator, Sequence
from contextlib import asynccontextmanager
from uuid import uuid4

import pytest
from dishka import Provider, Scope, make_async_container, provide
from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import SecretStr

from huerise.features.events.application import EventStreamHub
from huerise.features.events.domain import HueriseEvent
from huerise.features.events.presentation import event_stream_router
from huerise.features.events.presentation.sse import format_frame
from huerise.infrastructure.auth import encode_access_token
from huerise.presentation import auth
from huerise.tests.events.conftest import make_created

SECRET = "test-jwt-secret"
TOKEN = encode_access_token(
    user_id=uuid4(), tenant_id=uuid4(), secret=SECRET, ttl_minutes=15
)
AUTH = {"Authorization": f"Bearer {TOKEN}"}


class FiniteHub:
    """A hub whose stream ends on its own, so a test can read it to completion."""

    def __init__(self, events: Sequence[HueriseEvent]) -> None:
        self.events = events
        self.last_event_id: str | None = None

    @asynccontextmanager
    async def subscribe(
        self, last_event_id: str | None = None
    ) -> AsyncGenerator[AsyncIterator[HueriseEvent]]:
        self.last_event_id = last_event_id

        async def stream() -> AsyncIterator[HueriseEvent]:
            for event in self.events:
                yield event

        yield stream()


class StubProvider(Provider):
    scope = Scope.APP

    def __init__(self, hub: FiniteHub) -> None:
        super().__init__()
        self._hub = hub

    @provide
    def event_stream_hub(self) -> EventStreamHub:
        return self._hub  # type: ignore[return-value]


@pytest.fixture
def hub() -> FiniteHub:
    return FiniteHub([make_created(), make_created()])


@pytest.fixture
def client(hub: FiniteHub, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setattr(auth._settings, "jwt_secret", SecretStr(SECRET))

    app = FastAPI()
    app.include_router(event_stream_router)
    setup_dishka(make_async_container(StubProvider(hub)), app=app)
    return TestClient(app)


def test_serves_the_stream_as_server_sent_events(client: TestClient) -> None:
    response = client.get("/eventstream", headers=AUTH)

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")


def test_streaming_proxies_are_told_not_to_buffer(client: TestClient) -> None:
    response = client.get("/eventstream", headers=AUTH)

    assert response.headers["cache-control"] == "no-cache"
    assert response.headers["x-accel-buffering"] == "no"


def test_body_is_the_framed_events(client: TestClient, hub: FiniteHub) -> None:
    response = client.get("/eventstream", headers=AUTH)

    assert response.text == "".join(format_frame(event) for event in hub.events)


def test_last_event_id_header_reaches_the_hub(
    client: TestClient, hub: FiniteHub
) -> None:
    client.get("/eventstream", headers={**AUTH, "Last-Event-ID": "abc123"})

    assert hub.last_event_id == "abc123"


def test_requires_the_access_token(client: TestClient) -> None:
    assert client.get("/eventstream").status_code == 401
