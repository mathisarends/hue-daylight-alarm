from dishka import Provider, Scope, provide

from huerise.features.alarm.domain import AlarmUnitOfWorkFactory
from huerise.features.events.application import EventPublisher
from huerise.features.lighting.application import Lights
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
        unit_of_work_factory: AlarmUnitOfWorkFactory,
        events: EventPublisher,
    ) -> AlarmRunnerPort:
        return AlarmRunner(
            lights=lights,
            unit_of_work_factory=unit_of_work_factory,
            events=events,
        )
