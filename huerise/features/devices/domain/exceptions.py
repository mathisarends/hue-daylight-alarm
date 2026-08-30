class DeviceError(Exception):
    """Base for everything the devices feature raises."""


class HueUnavailableError(DeviceError):
    """Hue was used before onboarding completed or while it is unavailable."""


class HueDiscoveryError(DeviceError):
    def __init__(self, reason: str = "No Hue Bridge could be discovered") -> None:
        super().__init__(reason)


class HueRegistrationError(DeviceError):
    pass


class HueLinkButtonTimeoutError(HueRegistrationError):
    def __init__(self) -> None:
        super().__init__("Hue Bridge link button was not pressed within 60 seconds")


class HueBridgeNotFoundError(DeviceError):
    def __init__(self, bridge_id: str) -> None:
        super().__init__(f"Hue Bridge '{bridge_id}' was not discovered")


class HueBridgeNotSelectedError(DeviceError):
    def __init__(self) -> None:
        super().__init__("Select a Hue Bridge before registering it")


class HueEnvironmentOverrideError(DeviceError):
    def __init__(self) -> None:
        super().__init__("Hue setup is controlled by HUE_BRIDGE_IP and HUE_APP_KEY")


class RoomNotFoundError(DeviceError):
    def __init__(self, room_id: str) -> None:
        super().__init__(f"Room '{room_id}' not found")


class SceneNotFoundError(DeviceError):
    def __init__(self, room_id: str, scene_id: str) -> None:
        super().__init__(f"Room '{room_id}' has no scene '{scene_id}'")
