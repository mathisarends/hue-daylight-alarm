from dishka import Provider, Scope, provide

from huerise.configuration import YamlConfiguration
from huerise.features.daylight_alarm.application import DaylightAlarm
from huerise.features.lighting.application import HueClientFactory
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
