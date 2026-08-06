from uuid import uuid4

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from pydantic import SecretStr

from huerise.infrastructure.auth import encode_access_token
from huerise.presentation import auth

SECRET = "test-jwt-secret"


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setattr(auth._settings, "jwt_secret", SecretStr(SECRET))

    app = FastAPI()

    @app.get("/protected", dependencies=[Depends(auth.get_current_user)])
    async def protected() -> dict[str, bool]:
        return {"ok": True}

    return TestClient(app)


def _make_token(secret: str = SECRET) -> str:
    return encode_access_token(
        user_id=uuid4(), tenant_id=uuid4(), secret=secret, ttl_minutes=15
    )


class TestGetCurrentUser:
    def test_accepts_a_validly_signed_token(self, client: TestClient) -> None:
        response = client.get(
            "/protected", headers={"Authorization": f"Bearer {_make_token()}"}
        )

        assert response.status_code == 200

    def test_rejects_a_request_without_a_header(self, client: TestClient) -> None:
        response = client.get("/protected")

        assert response.status_code == 401
        assert response.headers["WWW-Authenticate"] == "Bearer"

    def test_rejects_a_garbage_token(self, client: TestClient) -> None:
        response = client.get(
            "/protected", headers={"Authorization": "Bearer nope"}
        )

        assert response.status_code == 401

    def test_rejects_a_token_signed_with_the_wrong_secret(
        self, client: TestClient
    ) -> None:
        response = client.get(
            "/protected",
            headers={"Authorization": f"Bearer {_make_token('wrong-secret')}"},
        )

        assert response.status_code == 401

    def test_rejects_a_non_bearer_scheme(self, client: TestClient) -> None:
        response = client.get(
            "/protected", headers={"Authorization": f"Basic {_make_token()}"}
        )

        assert response.status_code == 401
