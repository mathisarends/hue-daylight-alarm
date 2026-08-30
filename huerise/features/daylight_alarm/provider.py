from dishka import Provider, Scope, provide

from huerise.configuration import YamlConfiguration
from huerise.features.daylight_alarm.service import DaylightAlarm
from huerise.features.lighting.hue import HueClientFactory, HueCredentialsProvider


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
