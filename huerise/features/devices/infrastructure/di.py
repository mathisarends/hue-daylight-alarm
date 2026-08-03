from dishka import Provider, Scope, provide
from hueify import Hueify

from huerise.features.devices.application import (
    AudioPlayer,
    Lights,
    SoundCatalog,
    SoundService,
)
from huerise.features.devices.infrastructure.hue import HueLights
from huerise.features.devices.infrastructure.settings import HueCredentials
from huerise.features.devices.infrastructure.sound_device import SoundDeviceAudioPlayer
from huerise.infrastructure.storage import StorageBackend


class DevicesProvider(Provider):
    scope = Scope.APP

    @provide
    def hue_credentials(self) -> HueCredentials:
        return HueCredentials()

    @provide
    def lights(self, credentials: HueCredentials) -> Lights:
        return HueLights(
            Hueify(credentials.bridge_ip, credentials.app_key.get_secret_value())
        )

    @provide
    def sound_catalog(self, storage: StorageBackend) -> SoundCatalog:
        return SoundCatalog(storage)

    @provide
    def audio(self, catalog: SoundCatalog, storage: StorageBackend) -> AudioPlayer:
        return SoundDeviceAudioPlayer(catalog, storage)

    @provide(scope=Scope.REQUEST)
    def sound_service(self, catalog: SoundCatalog, audio: AudioPlayer) -> SoundService:
        return SoundService(catalog, audio)
