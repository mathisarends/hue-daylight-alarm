from pathlib import Path

from fastapi import APIRouter

from backend.src.infrastructure.audio.registry import AudioRegistry, RegisteredSound

router = APIRouter(prefix="/sounds", tags=["Sounds"])

# Relativer Pfad zum assets Ordner
SOUNDS_DIR = Path(__file__).parent.parent.parent / "assets"

audio_registry = AudioRegistry(SOUNDS_DIR)


@router.get("", response_model=list[RegisteredSound])
def list_sounds():
    sounds = audio_registry.get_all()

    return [
        RegisteredSound(
            name=sound.name,
            relative_path=sound.relative_path,
            category=sound.category,
        )
        for sound in sounds
    ]
