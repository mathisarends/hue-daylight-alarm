import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from pydantic import SecretStr

from huerise.presentation import auth

TOKEN = "test-access-token"


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setattr(auth._settings, "access_token", SecretStr(TOKEN))

    app = FastAPI()

    @app.get("/protected", dependencies=[Depends(auth.require_access_token)])
    async def protected() -> dict[str, bool]:
        return {"ok": True}

    return TestClient(app)


class TestRequireAccessToken:
    def test_accepts_the_configured_token(self, client: TestClient) -> None:
        response = client.get(
            "/protected", headers={"Authorization": f"Bearer {TOKEN}"}
        )

        assert response.status_code == 200

    def test_rejects_a_request_without_a_header(self, client: TestClient) -> None:
        response = client.get("/protected")

        assert response.status_code == 401
        assert response.headers["WWW-Authenticate"] == "Bearer"

    def test_rejects_a_wrong_token(self, client: TestClient) -> None:
        response = client.get("/protected", headers={"Authorization": "Bearer nope"})

        assert response.status_code == 401

    def test_rejects_a_non_bearer_scheme(self, client: TestClient) -> None:
        response = client.get("/protected", headers={"Authorization": f"Basic {TOKEN}"})

        assert response.status_code == 401
