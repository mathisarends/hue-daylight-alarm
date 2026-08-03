from dishka import Provider, Scope, provide

from huerise.features.alarm.domain import AlarmUnitOfWorkFactory
from huerise.features.runner.application.runner_port import AlarmRunner
from huerise.features.scheduler.application import AlarmScheduler


class SchedulerProvider(Provider):
    scope = Scope.APP

    @provide
    def alarm_scheduler(
        self,
        unit_of_work_factory: AlarmUnitOfWorkFactory,
        runner: AlarmRunner,
    ) -> AlarmScheduler:
        return AlarmScheduler(
            unit_of_work_factory=unit_of_work_factory,
            runner=runner,
        )
