from dishka import Provider, Scope, provide

from huerise.configuration import HueEnvironment, YamlConfiguration
from huerise.features.daylight_alarm.service import DaylightAlarm
from huerise.features.lighting.doctor import Doctor
from huerise.features.lighting.hue import (
    HueClientFactory,
    HueCredentialsProvider,
    HueifyClientFactory,
)
from huerise.features.lighting.onboarding import (
    HueifyOnboarding,
    HueOnboarding,
    OnboardingGateway,
)
from huerise.features.lighting.services import SceneService


class LightingProvider(Provider):
    scope = Scope.APP

    @provide
    def client_factory(self) -> HueClientFactory:
        return HueifyClientFactory()

    @provide
    def credentials(
        self,
        configuration: YamlConfiguration,
        environment: HueEnvironment,
    ) -> HueCredentialsProvider:
        return HueCredentialsProvider(configuration, environment)

    @provide
    def onboarding_gateway(self) -> OnboardingGateway:
        return HueifyOnboarding()

    @provide
    def onboarding(
        self,
        configuration: YamlConfiguration,
        environment: HueEnvironment,
        gateway: OnboardingGateway,
    ) -> HueOnboarding:
        return HueOnboarding(configuration, environment, gateway)

    @provide
    def doctor(
        self,
        configuration: YamlConfiguration,
        credentials: HueCredentialsProvider,
        clients: HueClientFactory,
    ) -> Doctor:
        return Doctor(configuration, credentials, clients)

    @provide
    def scenes(
        self,
        credentials: HueCredentialsProvider,
        clients: HueClientFactory,
        alarm: DaylightAlarm,
    ) -> SceneService:
        return SceneService(credentials, clients, alarm)
