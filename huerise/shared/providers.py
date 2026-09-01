from dishka import Provider, Scope, provide

from huerise.configuration import YamlConfiguration
from huerise.env import AppSettings, HueEnvironment


class CoreProvider(Provider):
    scope = Scope.APP

    @provide
    def app_settings(self) -> AppSettings:
        return AppSettings()

    @provide
    def hue_environment(self) -> HueEnvironment:
        return HueEnvironment()

    @provide
    def configuration(self, settings: AppSettings) -> YamlConfiguration:
        return YamlConfiguration(settings.config_path)
