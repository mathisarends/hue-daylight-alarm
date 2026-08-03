from dishka import Provider, Scope, provide
from hueify import Hueify

from huerise.features.devices.application import AudioPlayer, Lights
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
    def audio(self, storage: StorageBackend) -> AudioPlayer:
        return SoundDeviceAudioPlayer(storage)
