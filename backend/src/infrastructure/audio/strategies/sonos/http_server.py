from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path

app = FastAPI()

SOUNDS_DIR = Path("assets/wake_up_sounds")


@app.get("/sounds/{sound_name}")
async def get_sound(sound_name: str):
    file_path = SOUNDS_DIR / sound_name

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Sound not found")

    return FileResponse(
        file_path,
        media_type="audio/mpeg",
        headers={"Cache-Control": "public, max-age=3600", "Accept-Ranges": "bytes"},
    )
