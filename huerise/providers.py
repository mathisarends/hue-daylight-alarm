from dishka import Provider, Scope, provide

from huerise.configuration import (
    APISettings,
    HueEnvironment,
    YamlConfiguration,
)


class CoreProvider(Provider):
    scope = Scope.APP

    @provide
    def api_settings(self) -> APISettings:
        return APISettings()

    @provide
    def hue_environment(self) -> HueEnvironment:
        return HueEnvironment()

    @provide
    def configuration(self, settings: APISettings) -> YamlConfiguration:
        return YamlConfiguration(settings.config_path)
