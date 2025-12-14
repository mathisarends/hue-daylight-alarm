from fastapi import APIRouter

from backend.dependencies import InjectedAudioRegistry
from backend.src.infrastructure.audio import RegisteredSound

router = APIRouter(prefix="/sounds", tags=["Sounds"])


@router.get("", response_model=list[RegisteredSound])
def list_all_sounds(audio_registry: InjectedAudioRegistry):
    sounds = audio_registry.get_all()
    return [
        RegisteredSound(
            name=sound.name,
            relative_path=sound.relative_path,
            category=sound.category,
        )
        for sound in sounds
    ]


@router.get("/wake-up", response_model=list[RegisteredSound])
def list_wake_up_sounds(audio_registry: InjectedAudioRegistry):
    sounds = audio_registry.get_wake_up_sounds()
    return [
        RegisteredSound(
            name=sound.name,
            relative_path=sound.relative_path,
            category=sound.category,
        )
        for sound in sounds
    ]


@router.get("/get-up", response_model=list[RegisteredSound])
def list_get_up_sounds(audio_registry: InjectedAudioRegistry):
    sounds = audio_registry.get_get_up_sounds()
    return [
        RegisteredSound(
            name=sound.name,
            relative_path=sound.relative_path,
            category=sound.category,
        )
        for sound in sounds
    ]
