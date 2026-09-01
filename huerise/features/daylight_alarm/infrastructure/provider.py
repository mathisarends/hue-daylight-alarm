from dishka import Provider, Scope, provide

from huerise.configuration import YamlConfiguration
from huerise.features.daylight_alarm.application import (
    DaylightAlarm,
    DaylightAlarmConfiguration,
)
from huerise.features.lighting.application import HueClientFactory, SceneService
from huerise.features.lighting.infrastructure import HueCredentialsProvider


class DaylightAlarmProvider(Provider):
    scope = Scope.APP

    @provide
    def daylight_alarm(
        self,
        configuration: YamlConfiguration,
        credentials: HueCredentialsProvider,
        clients: HueClientFactory,
    ) -> DaylightAlarm:
        return DaylightAlarm(configuration, credentials, clients)

    @provide
    def configuration(
        self,
        configuration: YamlConfiguration,
        scenes: SceneService,
    ) -> DaylightAlarmConfiguration:
        return DaylightAlarmConfiguration(configuration, scenes)
