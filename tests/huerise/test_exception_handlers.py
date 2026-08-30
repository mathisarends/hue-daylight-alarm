from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from huerise.configuration import ConfigurationError, ConfigurationIssue
from huerise.exception_handlers import ExceptionRouter, error


def test_preserves_configuration_issues_in_route_error_response() -> None:
    router = ExceptionRouter()

    @router.get(
        "/configuration",
        errors={
            ConfigurationError: error(
                status.HTTP_422_UNPROCESSABLE_CONTENT,
                "The configuration is invalid.",
            )
        },
    )
    async def configuration() -> None:
        raise ConfigurationError(
            "Configuration is invalid",
            [
                ConfigurationIssue(
                    location="daylight_alarm.scene_id",
                    message="Field required",
                    type="missing",
                )
            ],
        )

    app = FastAPI()
    app.include_router(router)

    response = TestClient(app).get("/configuration")

    assert response.status_code == 422
    assert response.json() == {
        "detail": "Configuration is invalid",
        "issues": [
            {
                "location": "daylight_alarm.scene_id",
                "message": "Field required",
                "type": "missing",
            }
        ],
    }
