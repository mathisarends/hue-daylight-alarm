from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/sound-profiles", tags=["Sound Profiles"])

MOCK_PROFILES = [
    {
        "name": "peaceful",
        "display_name": "Peaceful Morning",
        "description": "Sanfte Klangschalen und blumige Melodien",
        "wake_up_sound": "wake-up-bowls.mp3",
        "get_up_sound": "get-up-blossom.mp3",
    },
    {
        "name": "energetic",
        "display_name": "Energetic Start",
        "description": "Kraftvolle Klänge für dynamischen Start",
        "wake_up_sound": "wake-up-gong.mp3",
        "get_up_sound": "get-up-shake.mp3",
    },
    {
        "name": "nature",
        "display_name": "Nature Awakening",
        "description": "Natürliche Klänge aus dem Dschungel",
        "wake_up_sound": "wake-up-jungle.mp3",
        "get_up_sound": "get-up-retreat.mp3",
    },
    {
        "name": "cosmic",
        "display_name": "Cosmic Journey",
        "description": "Sphärische Klänge aus dem Universum",
        "wake_up_sound": "wake-up-galaxy.mp3",
        "get_up_sound": "get-up-aurora.mp3",
    },
]


@router.get("")
def list_sound_profiles():
    return {"profiles": MOCK_PROFILES}


@router.get("/{name}")
def get_sound_profile(name: str):
    profile = next((p for p in MOCK_PROFILES if p["name"] == name), None)
    if not profile:
        raise HTTPException(status_code=404, detail=f"Sound profile '{name}' not found")
    return profile
