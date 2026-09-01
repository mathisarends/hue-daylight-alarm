from fastapi import status

from huerise.configuration import ConfigurationError
from huerise.exception_handlers import error
from huerise.features.daylight_alarm.application import (
    AlarmAlreadyRunningError,
    SceneDoesNotBelongToRoomError,
)
from huerise.features.lighting.application import (
    HueUnavailableError,
    SceneNotFoundError,
)

start_alarm_errors = {
    AlarmAlreadyRunningError: error(
        status.HTTP_409_CONFLICT,
        "A daylight alarm is already running.",
    ),
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

configuration_errors = {
    SceneDoesNotBelongToRoomError: error(
        status.HTTP_422_UNPROCESSABLE_CONTENT,
        "The selected scene does not belong to the selected room.",
    ),
    SceneNotFoundError: error(
        status.HTTP_404_NOT_FOUND,
        "The selected Hue scene does not exist.",
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
