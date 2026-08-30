from fastapi import status

from huerise.configuration import ConfigurationError
from huerise.exception_handlers import error
from huerise.features.lighting.application import (
    BridgeNotFoundError,
    BridgeNotSelectedError,
    HueUnavailableError,
    LinkButtonTimeoutError,
    OnboardingReadOnlyError,
    SceneNotFoundError,
)

doctor_errors = {
    SceneNotFoundError: error(
        status.HTTP_404_NOT_FOUND,
        "The configured Hue scene does not exist.",
    ),
    ConfigurationError: error(
        status.HTTP_422_UNPROCESSABLE_CONTENT,
        "The YAML configuration is missing or invalid.",
    ),
    HueUnavailableError: error(
        status.HTTP_503_SERVICE_UNAVAILABLE,
        "The Hue Bridge is not configured, reachable, or authenticated.",
    ),
}

discover_bridges_errors = {
    ConfigurationError: error(
        status.HTTP_422_UNPROCESSABLE_CONTENT,
        "The stored Hue configuration is invalid.",
    ),
    HueUnavailableError: error(
        status.HTTP_503_SERVICE_UNAVAILABLE,
        "Hue Bridge discovery is unavailable.",
    ),
}

bridge_status_errors = {
    ConfigurationError: error(
        status.HTTP_422_UNPROCESSABLE_CONTENT,
        "The stored Hue configuration is invalid.",
    ),
}

select_bridge_errors = {
    BridgeNotFoundError: error(
        status.HTTP_404_NOT_FOUND,
        "The selected Hue Bridge was not discovered.",
    ),
    OnboardingReadOnlyError: error(
        status.HTTP_409_CONFLICT,
        "Environment overrides make Hue onboarding read-only.",
    ),
    **discover_bridges_errors,
}

register_bridge_errors = {
    BridgeNotSelectedError: error(
        status.HTTP_409_CONFLICT,
        "A Hue Bridge must be selected before registration.",
    ),
    LinkButtonTimeoutError: error(
        status.HTTP_409_CONFLICT,
        "The Hue Bridge link button was not pressed in time.",
    ),
    OnboardingReadOnlyError: error(
        status.HTTP_409_CONFLICT,
        "Environment overrides make Hue onboarding read-only.",
    ),
    ConfigurationError: error(
        status.HTTP_422_UNPROCESSABLE_CONTENT,
        "The stored Hue configuration is invalid.",
    ),
    HueUnavailableError: error(
        status.HTTP_503_SERVICE_UNAVAILABLE,
        "Hue Bridge registration is unavailable.",
    ),
}

scene_errors = {
    ConfigurationError: error(
        status.HTTP_422_UNPROCESSABLE_CONTENT,
        "The YAML configuration is invalid.",
    ),
    HueUnavailableError: error(
        status.HTTP_503_SERVICE_UNAVAILABLE,
        "The Hue Bridge is not configured, reachable, or authenticated.",
    ),
}
