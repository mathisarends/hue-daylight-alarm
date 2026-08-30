from uuid import UUID

from hueify import Hueify
from hueify.onboarding import discover_bridges, register_app_key

from huerise.configuration import HueEnvironment, YamlConfiguration
from huerise.features.lighting.application.models import (
    HueClient,
    HueCredentials,
    HueUnavailableError,
    Room,
    Scene,
)
from huerise.features.lighting.application.onboarding import (
    HueBridge,
    OnboardingGateway,
)


class HueCredentialsProvider:
    def __init__(
        self, configuration: YamlConfiguration, environment: HueEnvironment
    ) -> None:
        self._configuration = configuration
        self._environment = environment

    def get(self) -> HueCredentials:
        if self._environment.configured:
            assert self._environment.bridge_ip is not None
            assert self._environment.app_key is not None
            return HueCredentials(
                bridge_ip=str(self._environment.bridge_ip),
                app_key=self._environment.app_key.get_secret_value(),
            )

        hue = self._configuration.load_hue()
        if hue is None or hue.app_key is None:
            raise HueUnavailableError("Philips Hue Bridge is not configured")
        return HueCredentials(bridge_ip=str(hue.bridge_ip), app_key=hue.app_key)


class HueifyClientFactory:
    def create(self, credentials: HueCredentials) -> HueClient:
        return HueifyClient(Hueify(credentials.bridge_ip, credentials.app_key))


class HueifyClient:
    def __init__(self, client: Hueify) -> None:
        self._client = client

    async def list_rooms(self) -> list[Room]:
        rooms = (await self._client.rooms.list()).data
        return [
            Room(
                id=room.id,
                name=room.name,
                scenes=tuple(
                    Scene(id=scene.id, name=scene.name)
                    for scene in await self._client.rooms.scenes(room.id)
                ),
            )
            for room in rooms
        ]

    async def activate_scene(self, scene_id: UUID, *, brightness: float) -> None:
        await self._client.scenes.activate(scene_id, brightness=brightness)

    async def set_brightness(self, room_id: UUID, brightness: float) -> None:
        await self._client.rooms.set_brightness(room_id, brightness)

    async def close(self) -> None:
        await self._client.close()


class HueifyOnboarding(OnboardingGateway):
    async def discover(self) -> tuple[HueBridge, ...]:
        return tuple(
            HueBridge(item.id, item.internalipaddress)
            for item in await discover_bridges()
        )

    async def register(self, bridge_ip: str) -> str:
        return await register_app_key(bridge_ip, device_type="huerise#backend")
