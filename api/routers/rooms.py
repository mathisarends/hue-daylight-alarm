from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/rooms", tags=["Rooms"])

MOCK_ROOMS = [
    {"name": "Zimmer 1", "id": "room-1", "type": "Bedroom"},
    {"name": "Wohnzimmer", "id": "room-2", "type": "Living room"},
    {"name": "Küche", "id": "room-3", "type": "Kitchen"},
]

MOCK_SCENES = {
    "Zimmer 1": [
        {"name": "Tageslichtwecker", "id": "scene-1"},
        {"name": "Entspannen", "id": "scene-2"},
        {"name": "Konzentrieren", "id": "scene-3"},
    ],
    "Wohnzimmer": [
        {"name": "Gemütlich", "id": "scene-4"},
        {"name": "Hell", "id": "scene-5"},
    ],
    "Küche": [
        {"name": "Kochen", "id": "scene-6"},
    ],
}


@router.get("")
def list_rooms():
    """Liste alle Hue-Räume."""
    return {"rooms": MOCK_ROOMS}


@router.get("/{room_name}")
def get_room(room_name: str):
    """Hole Raum-Details."""
    room = next((r for r in MOCK_ROOMS if r["name"] == room_name), None)
    if not room:
        raise HTTPException(status_code=404, detail=f"Room '{room_name}' not found")
    return room


@router.get("/{room_name}/scenes")
def list_room_scenes(room_name: str):
    """Liste Szenen für einen Raum."""
    if room_name not in MOCK_SCENES:
        raise HTTPException(status_code=404, detail=f"Room '{room_name}' not found")

    return {"room_name": room_name, "scenes": MOCK_SCENES[room_name]}
