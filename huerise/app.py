from dishka import AsyncContainer, Provider, make_async_container
from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI

from huerise.features import FEATURES
from huerise.infrastructure.di import DatabaseProvider, StorageProvider
from huerise.lifespan import lifespan

INFRASTRUCTURE_PROVIDERS: tuple[type[Provider], ...] = (
    DatabaseProvider,
    StorageProvider,
)

_TITLE = "Huerise Alarm API"
_VERSION = "1.0.0"
_DESCRIPTION = (
    "API for managing sunrise alarms with Philips Hue. "
    "Every endpoint requires an `Authorization: Bearer <token>` header."
)


def _create_container() -> AsyncContainer:
    provider_types = [
        *INFRASTRUCTURE_PROVIDERS,
        *(provider for feature in FEATURES for provider in feature.providers),
    ]
    return make_async_container(*(provider() for provider in provider_types))


def create_app() -> FastAPI:
    app = FastAPI(
        title=_TITLE,
        version=_VERSION,
        description=_DESCRIPTION,
        lifespan=lifespan,
    )

    setup_dishka(_create_container(), app=app)
    for feature in FEATURES:
        feature.install(app)

    return app
