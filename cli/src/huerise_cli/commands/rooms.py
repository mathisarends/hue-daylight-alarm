import typer

from huerise_cli.client import api_client
from huerise_cli.config import Config
from huerise_cli.generated.api.rooms_scenes import (
    activate_scene as activate_scene_api,
)
from huerise_cli.generated.api.rooms_scenes import (
    get_room as get_room_api,
)
from huerise_cli.generated.api.rooms_scenes import (
    list_rooms as list_rooms_api,
)
from huerise_cli.generated.models import RoomRead
from huerise_cli.output import (
    JsonOption,
    console,
    emit_json,
    emit_record,
    emit_table,
    unwrap,
)

app = typer.Typer(no_args_is_help=True, help="Browse rooms and Hue scenes.")


def _room_row(room: RoomRead) -> dict[str, object]:
    return {"name": room.name, "scenes": ", ".join(room.scene_names)}


@app.command("list")
def list_rooms(json_: JsonOption = False) -> None:
    """List every room Hue knows about."""
    with api_client(Config.from_env()) as client:
        rooms = unwrap(list_rooms_api.sync_detailed(client=client))

    if json_:
        emit_json([room.to_dict() for room in rooms])
    else:
        emit_table([_room_row(room) for room in rooms], empty_message="No rooms found.")


@app.command("get")
def get_room(room_name: str, json_: JsonOption = False) -> None:
    """Show a room and the scenes it offers."""
    with api_client(Config.from_env()) as client:
        room = unwrap(get_room_api.sync_detailed(client=client, room_name=room_name))

    if json_:
        emit_json(room.to_dict())
    else:
        emit_record(_room_row(room))


@app.command("activate-scene")
def activate_scene(room_name: str, scene_name: str) -> None:
    """Preview a scene the way an alarm would start it."""
    with api_client(Config.from_env()) as client:
        unwrap(
            activate_scene_api.sync_detailed(
                client=client, room_name=room_name, scene_name=scene_name
            )
        )
    console.print(f"[green]Activated '{scene_name}' in {room_name}.[/green]")
