from fastapi import status

from huerise.exception_handlers import error

configured_scene_not_found = error(
    status.HTTP_404_NOT_FOUND,
    "The configured Hue scene does not exist.",
)
invalid_yaml_configuration = error(
    status.HTTP_422_UNPROCESSABLE_CONTENT,
    "The YAML configuration is missing or invalid.",
)
unavailable_hue_bridge = error(
    status.HTTP_503_SERVICE_UNAVAILABLE,
    "The Hue Bridge is not configured, reachable, or authenticated.",
)
invalid_stored_hue_configuration = error(
    status.HTTP_422_UNPROCESSABLE_CONTENT,
    "The stored Hue configuration is invalid.",
)
unavailable_hue_discovery = error(
    status.HTTP_503_SERVICE_UNAVAILABLE,
    "Hue Bridge discovery is unavailable.",
)
selected_hue_bridge_not_found = error(
    status.HTTP_404_NOT_FOUND,
    "The selected Hue Bridge was not discovered.",
)
hue_onboarding_read_only = error(
    status.HTTP_409_CONFLICT,
    "Environment overrides make Hue onboarding read-only.",
)
hue_bridge_not_selected = error(
    status.HTTP_409_CONFLICT,
    "A Hue Bridge must be selected before registration.",
)
hue_link_button_timeout = error(
    status.HTTP_409_CONFLICT,
    "The Hue Bridge link button was not pressed in time.",
)
unavailable_hue_registration = error(
    status.HTTP_503_SERVICE_UNAVAILABLE,
    "Hue Bridge registration is unavailable.",
)
invalid_scene_configuration = error(
    status.HTTP_422_UNPROCESSABLE_CONTENT,
    "The YAML configuration is invalid.",
)
