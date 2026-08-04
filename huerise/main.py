from huerise.app import create_app

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
