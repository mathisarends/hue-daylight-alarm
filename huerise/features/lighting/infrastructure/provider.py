from dishka import Provider, Scope, provide

from huerise.configuration import YamlConfiguration
from huerise.env import HueEnvironment
from huerise.features.lighting.application import (
    Doctor,
    HueClientFactory,
    HueOnboarding,
    OnboardingGateway,
    SceneService,
)
from huerise.features.lighting.infrastructure.hue import (
    HueCredentialsProvider,
    HueifyClientFactory,
    HueifyOnboarding,
)


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
    ) -> SceneService:
        return SceneService(credentials, clients)
