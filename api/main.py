from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers import alarm_router, room_router, sound_router

app = FastAPI(
    title="Daylight Alarm API",
    description="API for controlling Hue-based daylight alarm clocks",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(alarm_router)
app.include_router(room_router)
app.include_router(sound_router)


@app.get("/", tags=["Root"])
def root():
    return {
        "name": "Daylight Alarm API",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "alarms": "/alarms",
            "rooms": "/rooms",
            "sound_profiles": "/sound-profiles",
        },
    }


@app.get("/health", tags=["Health"])
def health():
    return {"status": "healthy"}
