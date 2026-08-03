from dishka import Provider, Scope, provide

from huerise.features.alarm.domain import AlarmUnitOfWorkFactory
from huerise.features.devices.application import AudioPlayer, Lights
from huerise.features.runner.application import AlarmRunner
from huerise.features.runner.application.runner_port import (
    AlarmRunner as AlarmRunnerPort,
)


class RunnerProvider(Provider):
    scope = Scope.APP

    @provide
    def alarm_runner(
        self,
        lights: Lights,
        audio: AudioPlayer,
        unit_of_work_factory: AlarmUnitOfWorkFactory,
    ) -> AlarmRunnerPort:
        return AlarmRunner(
            lights=lights,
            audio=audio,
            unit_of_work_factory=unit_of_work_factory,
        )
