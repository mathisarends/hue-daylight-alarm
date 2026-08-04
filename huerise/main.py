import logging

from huerise.app import create_app

# Uvicorn only attaches handlers to its own loggers, so without this the root
# logger falls back to lastResort (WARNING) and every INFO record is dropped.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

app = create_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "huerise.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        loop="asyncio",
    )
