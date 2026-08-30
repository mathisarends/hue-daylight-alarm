from dishka import Provider, Scope, provide
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from huerise.features.lighting.application import (
    DoctorService,
    HueBridgeService,
    LightEvents,
    Lights,
    SceneService,
    SunriseDemoRunner,
)
from huerise.features.lighting.application.ports import HueOnboarding
from huerise.features.lighting.domain import HueBridgeRepository
from huerise.features.lighting.infrastructure.hue import (
    ConfigurableHue,
    HueifyOnboarding,
)
from huerise.features.lighting.infrastructure.persistence import SQLHueBridgeRepository
from huerise.features.lighting.infrastructure.settings import HueEnvironment


class LightingProvider(Provider):
    scope = Scope.APP

    @provide
    def hue_environment(self) -> HueEnvironment:
        return HueEnvironment()

    @provide
    def hue_bridge_repository(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> HueBridgeRepository:
        return SQLHueBridgeRepository(session_factory)

    @provide
    def configurable_hue(
        self,
        repository: HueBridgeRepository,
        environment: HueEnvironment,
        onboarding: HueOnboarding,
    ) -> ConfigurableHue:
        return ConfigurableHue(repository, environment, onboarding)

    @provide
    def hue_onboarding(self) -> HueOnboarding:
        return HueifyOnboarding()

    @provide
    def lights(self, hue: ConfigurableHue) -> Lights:
        return hue

    @provide
    def light_events(self, hue: ConfigurableHue) -> LightEvents:
        return hue

    @provide(scope=Scope.REQUEST)
    def hue_bridge_service(
        self,
        repository: HueBridgeRepository,
        connection: ConfigurableHue,
        environment: HueEnvironment,
        onboarding: HueOnboarding,
    ) -> HueBridgeService:
        return HueBridgeService(repository, connection, environment, onboarding)

    @provide(scope=Scope.REQUEST)
    def doctor_service(self, hue: HueBridgeService) -> DoctorService:
        return DoctorService(hue)

    @provide
    def sunrise_demo(self, lights: Lights) -> SunriseDemoRunner:
        """App-scoped: a demo keeps running after its request is answered."""
        return SunriseDemoRunner(lights)

    @provide(scope=Scope.REQUEST)
    def scene_service(self, lights: Lights, demo: SunriseDemoRunner) -> SceneService:
        return SceneService(lights, demo)
