from contextlib import asynccontextmanager
from fastapi import FastAPI

from backend.src.infrastructure.persistence.database import db_config

from backend.routers import api_v1


@asynccontextmanager
async def lifespan(app: FastAPI):
    db_config.create_tables()
    yield
    db_config.engine.dispose()


app = FastAPI(
    title="Daylight Alarm API",
    version="1.0.0",
    description="API for managing sunrise alarms with Philips Hue",
    lifespan=lifespan,
)

app.include_router(api_v1)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
