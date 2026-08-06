import logging
from collections.abc import AsyncIterator

from dishka import Provider, Scope, alias, provide
from hueify import Hueify
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from huerise.features.devices.application import (
    AudioOutputService,
    AudioPlayer,
    LightEvents,
    Lights,
    SceneService,
    SonosSpeakerService,
    SoundService,
    SunriseDemoRunner,
    SwitchableAudioPlayer,
)
from huerise.features.devices.domain import (
    AudioOutput,
    AudioOutputUnavailableError,
    SonosSpeakerRepository,
    SoundRepository,
)
from huerise.features.devices.infrastructure.hue import HueLightEvents, HueLights
from huerise.features.devices.infrastructure.persistence import (
    SQLSonosSpeakerRepository,
    SQLSoundRepository,
)
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
    def light_events(self, hue: Hueify) -> LightEvents:
        return HueLightEvents(hue)

    @provide
    def sound_repository(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> SoundRepository:
        return SQLSoundRepository(session_factory)

    @provide
    def sonos_speaker_repository(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> SonosSpeakerRepository:
        return SQLSonosSpeakerRepository(session_factory)

    @provide
    def audio_settings(self) -> AudioSettings:
        return AudioSettings()

    @provide
    def sonos_settings(self) -> SonosSettings:
        return SonosSettings()

    @provide
    async def switchable_audio(
        self,
        sounds: SoundRepository,
        storage: StorageBackend,
        settings: AudioSettings,
        sonos_settings: SonosSettings,
        sonos_speaker_repository: SonosSpeakerRepository,
    ) -> AsyncIterator[SwitchableAudioPlayer]:
        """Build only configured adapters and own their app-scoped resources."""
        players: dict[AudioOutput, AudioPlayer] = {}
        sonos_player = None

        if AudioOutput.LOCAL in settings.backends:
            # Optional audio libraries stay out of Sonos-only processes.
            from huerise.features.devices.infrastructure.sound_device import (
                SoundDeviceAudioPlayer,
            )

            players[AudioOutput.LOCAL] = SoundDeviceAudioPlayer(sounds, storage)

        if AudioOutput.SONOS in settings.backends:
            # sonosify and its UPnP stack stay out of local-only processes.
            from sonosify import SonosController

            from huerise.features.devices.infrastructure.sonos import SonosAudioPlayer

            controller = SonosController(
                discovery_timeout=sonos_settings.discovery_timeout
            )
            sonos_player = SonosAudioPlayer(sounds, storage, controller)
            saved_speaker = await sonos_speaker_repository.get_selected()
            if saved_speaker is not None:
                try:
                    speaker = await sonos_player.restore_speaker(saved_speaker)
                except AudioOutputUnavailableError as error:
                    logger.warning("Could not restore Sonos speaker: %s", error)
                else:
                    logger.info(
                        "Restored Sonos speaker %s at %s",
                        speaker.name,
                        speaker.ip_address,
                    )
            elif sonos_settings.speaker_name or sonos_settings.ip_address:
                speaker = await sonos_player.configure(
                    sonos_settings.speaker_name, sonos_settings.ip_address
                )
                await sonos_speaker_repository.save_selected(speaker)
                logger.info(
                    "Connected to Sonos speaker %s at %s",
                    speaker.name,
                    speaker.ip_address,
                )
            players[AudioOutput.SONOS] = sonos_player

        try:
            yield SwitchableAudioPlayer(players, active=settings.initial_output)
        finally:
            if sonos_player is not None:
                await sonos_player.close()

    audio = alias(source=SwitchableAudioPlayer, provides=AudioPlayer)

    @provide
    def sunrise_demo(self, lights: Lights) -> SunriseDemoRunner:
        """App-scoped: a demo keeps running after its request is answered."""
        return SunriseDemoRunner(lights)

    @provide(scope=Scope.REQUEST)
    def scene_service(self, lights: Lights, demo: SunriseDemoRunner) -> SceneService:
        return SceneService(lights, demo)

    @provide(scope=Scope.REQUEST)
    def sound_service(
        self, sounds: SoundRepository, audio: AudioPlayer
    ) -> SoundService:
        return SoundService(sounds, audio)

    @provide(scope=Scope.REQUEST)
    def audio_output_service(self, player: SwitchableAudioPlayer) -> AudioOutputService:
        return AudioOutputService(player)

    @provide(scope=Scope.REQUEST)
    def sonos_speaker_service(
        self,
        player: SwitchableAudioPlayer,
        sonos_speaker_repository: SonosSpeakerRepository,
    ) -> SonosSpeakerService:
        return SonosSpeakerService(player, sonos_speaker_repository)
