from dishka import make_async_container
from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI

from huerise.alarm import feature
from huerise.lifespan import lifespan

_container = make_async_container(*(provider() for provider in feature.providers))

app = FastAPI(
    title="Huerise Alarm API",
    version="1.0.0",
    description="API for managing sunrise alarms with Philips Hue",
    lifespan=lifespan,
)

setup_dishka(_container, app=app)
for router in feature.routers:
    app.include_router(router)
feature.register_exception_handlers(app)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("huerise.main:app", host="127.0.0.1", port=8000, reload=True)
