from dishka import Provider, make_async_container
from dishka.integrations.fastapi import setup_dishka
from fastapi import Depends, FastAPI

from huerise.features import alarm, devices, runner, scheduler
from huerise.infrastructure.di import DatabaseProvider, StorageProvider
from huerise.lifespan import lifespan
from huerise.presentation import require_access_token

_FEATURES = [alarm.feature, devices.feature, runner.feature, scheduler.feature]
_INFRASTRUCTURE_PROVIDERS = [DatabaseProvider, StorageProvider]

providers: list[Provider] = [provider() for provider in _INFRASTRUCTURE_PROVIDERS]
for feature in _FEATURES:
    providers.extend(provider() for provider in feature.providers)
_container = make_async_container(*providers)

app = FastAPI(
    title="Huerise Alarm API",
    version="1.0.0",
    description=(
        "API for managing sunrise alarms with Philips Hue. "
        "Every endpoint requires an `Authorization: Bearer <token>` header."
    ),
    lifespan=lifespan,
)

setup_dishka(_container, app=app)
for feature in _FEATURES:
    for router in feature.routers:
        app.include_router(router, dependencies=[Depends(require_access_token)])
    if feature.register_exception_handlers is not None:
        feature.register_exception_handlers(app)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("huerise.main:app", host="127.0.0.1", port=8000, reload=True)
