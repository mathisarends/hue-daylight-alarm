from dishka import Provider, Scope, provide

from huerise.infrastructure.storage import (
    S3StorageBackend,
    StorageBackend,
    StorageSettings,
)


class StorageProvider(Provider):
    scope = Scope.APP

    @provide
    def settings(self) -> StorageSettings:
        return StorageSettings()

    @provide
    def storage(self, settings: StorageSettings) -> StorageBackend:
        return S3StorageBackend(settings)
