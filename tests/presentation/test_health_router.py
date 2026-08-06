from unittest.mock import AsyncMock, MagicMock

import pytest
from dishka import Provider, Scope, make_async_container, provide
from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine

from huerise.presentation import health_router


class StubProvider(Provider):
    scope = Scope.APP

    def __init__(self, engine: AsyncEngine) -> None:
        super().__init__()
        self._engine = engine

    @provide
    def engine(self) -> AsyncEngine:
        return self._engine


@pytest.fixture
def engine() -> AsyncEngine:
    connection = AsyncMock()
    engine = MagicMock(spec=AsyncEngine)
    engine.connect.return_value.__aenter__.return_value = connection
    return engine


@pytest.fixture
def client(engine: AsyncEngine) -> TestClient:
    app = FastAPI()
    app.include_router(health_router)
    setup_dishka(make_async_container(StubProvider(engine)), app=app)
    return TestClient(app)


def test_health_reports_ok_without_checking_dependencies(
    client: TestClient, engine: AsyncEngine
) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    engine.connect.assert_not_called()


def test_readiness_checks_the_database(
    client: TestClient, engine: AsyncEngine
) -> None:
    response = client.get("/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    engine.connect.return_value.__aenter__.return_value.execute.assert_awaited_once()


def test_readiness_reports_an_unavailable_database(
    client: TestClient, engine: AsyncEngine
) -> None:
    connection = engine.connect.return_value.__aenter__.return_value
    connection.execute.side_effect = SQLAlchemyError("offline")

    response = client.get("/ready")

    assert response.status_code == 503
    assert response.json() == {"detail": "Database unavailable"}
