import logging
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
from huerise.features.devices.domain import AudioOutput, AudioOutputUnavailableError
from huerise.features.devices.infrastructure.hue import HueLights
from huerise.features.devices.infrastructure.settings import (
    AudioSettings,
    HueCredentials,
    SonosSettings,
)
from huerise.infrastructure.storage import StorageBackend

logger = logging.getLogger(__name__)


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
    async def switchable_audio(
        self,
        catalog: SoundCatalog,
        storage: StorageBackend,
        settings: AudioSettings,
        sonos_settings: SonosSettings,
    ) -> AsyncIterator[SwitchableAudioPlayer]:
        """Build only configured adapters and own their app-scoped resources."""
        players: dict[AudioOutput, AudioPlayer] = {}
        sonos_client = None

        if AudioOutput.LOCAL in settings.backends:
            # Optional audio libraries stay out of Sonos-only processes.
            from huerise.features.devices.infrastructure.sound_device import (
                SoundDeviceAudioPlayer,
            )

            players[AudioOutput.LOCAL] = SoundDeviceAudioPlayer(catalog, storage)

        if AudioOutput.SONOS in settings.backends:
            # sonosify and its UPnP stack stay out of local-only processes.
            from sonosify import SonosController, SonosifyError

            from huerise.features.devices.infrastructure.sonos import SonosAudioPlayer

            controller = SonosController(
                discovery_timeout=sonos_settings.discovery_timeout
            )
            try:
                sonos_client = await controller.client(
                    sonos_settings.speaker_name, ip=sonos_settings.ip_address
                )
            except SonosifyError as error:
                raise AudioOutputUnavailableError(
                    AudioOutput.SONOS, str(error)
                ) from error
            logger.info(
                "Connected to Sonos speaker %s at %s",
                await sonos_client.get_room_name(),
                sonos_client.ip,
            )
            players[AudioOutput.SONOS] = SonosAudioPlayer(
                catalog, storage, sonos_client
            )

        try:
            yield SwitchableAudioPlayer(players, active=settings.initial_output)
        finally:
            if sonos_client is not None:
                await sonos_client.close()

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
