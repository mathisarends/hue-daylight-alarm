from collections.abc import AsyncIterator

from dishka import Provider, Scope, alias, provide
from hueify import Hueify

from huerise.features.devices.application import (
    AudioOutputService,
    AudioPlayer,
    Lights,
    SceneService,
    SoundCatalog,
    SoundService,
    SwitchableAudioPlayer,
)
from huerise.features.devices.domain import AudioOutput
from huerise.features.devices.infrastructure.hue import HueLights
from huerise.features.devices.infrastructure.settings import (
    AudioSettings,
    HueCredentials,
    SonosSettings,
)
from huerise.features.devices.infrastructure.sonos import SonosAudioPlayer
from huerise.features.devices.infrastructure.sound_device import SoundDeviceAudioPlayer
from huerise.infrastructure.storage import StorageBackend


class DevicesProvider(Provider):
    scope = Scope.APP

    @provide
    def hue_credentials(self) -> HueCredentials:
        return HueCredentials()

    @provide
    async def hue(self, credentials: HueCredentials) -> AsyncIterator[Hueify]:
        """Connected client: its caches are only populated by ``connect()``."""
        async with Hueify(
            credentials.bridge_ip, credentials.app_key.get_secret_value()
        ) as hue:
            yield hue

    @provide
    def lights(self, hue: Hueify) -> Lights:
        return HueLights(hue)

    @provide
    def sound_catalog(self, storage: StorageBackend) -> SoundCatalog:
        return SoundCatalog(storage)

    @provide
    def audio_settings(self) -> AudioSettings:
        return AudioSettings()

    @provide
    def sonos_settings(self) -> SonosSettings:
        return SonosSettings()

    @provide
    def local_audio(
        self, catalog: SoundCatalog, storage: StorageBackend
    ) -> SoundDeviceAudioPlayer:
        return SoundDeviceAudioPlayer(catalog, storage)

    @provide
    async def sonos_audio(
        self,
        catalog: SoundCatalog,
        storage: StorageBackend,
        settings: SonosSettings,
    ) -> AsyncIterator[SonosAudioPlayer]:
        """Owns the speaker connection, so shutdown closes it."""
        player = SonosAudioPlayer(catalog, storage, settings)
        yield player
        await player.close()

    @provide
    def switchable_audio(
        self,
        local: SoundDeviceAudioPlayer,
        sonos: SonosAudioPlayer,
        settings: AudioSettings,
    ) -> SwitchableAudioPlayer:
        return SwitchableAudioPlayer(
            {AudioOutput.LOCAL: local, AudioOutput.SONOS: sonos},
            active=settings.default_output,
        )

    audio = alias(source=SwitchableAudioPlayer, provides=AudioPlayer)

    @provide(scope=Scope.REQUEST)
    def scene_service(self, lights: Lights) -> SceneService:
        return SceneService(lights)

    @provide(scope=Scope.REQUEST)
    def sound_service(self, catalog: SoundCatalog, audio: AudioPlayer) -> SoundService:
        return SoundService(catalog, audio)

    @provide(scope=Scope.REQUEST)
    def audio_output_service(self, player: SwitchableAudioPlayer) -> AudioOutputService:
        return AudioOutputService(player)
