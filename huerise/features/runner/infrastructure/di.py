from dishka import Provider, Scope, provide
from hueify import Hueify

from huerise.features.alarm.infrastructure.persistence import (
    BackgroundAlarmRepository,
)
from huerise.features.alarm.application import AudioPlayer
from huerise.features.runner.application import AlarmRunner, Lights
from huerise.features.runner.application.runner_port import (
    AlarmRunner as AlarmRunnerPort,
)
from huerise.features.runner.infrastructure.hue import HueLights
from huerise.features.runner.infrastructure.pyaudio import SoundDeviceAudioPlayer
from huerise.features.runner.infrastructure.settings import HueCredentials
from huerise.infrastructure.storage import StorageBackend


class RunnerProvider(Provider):
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

    @provide
    def alarm_runner(
        self,
        lights: Lights,
        audio: AudioPlayer,
        repo: BackgroundAlarmRepository,
    ) -> AlarmRunnerPort:
        return AlarmRunner(lights=lights, audio=audio, repo=repo)
