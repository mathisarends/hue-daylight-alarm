from typing import Annotated
from uuid import UUID

import typer

from huerise_cli.client import api_client
from huerise_cli.config import Config
from huerise_cli.generated.api.sounds import (
    list_sounds as list_sounds_api,
)
from huerise_cli.generated.api.sounds import (
    preview_sound as preview_sound_api,
)
from huerise_cli.generated.api.sounds import (
    set_volume as set_volume_api,
)
from huerise_cli.generated.api.sounds import (
    stop_playback as stop_playback_api,
)
from huerise_cli.generated.models import (
    SoundCategory,
    SoundPreviewRequest,
    SoundRead,
    VolumeRequest,
)
from huerise_cli.output import JsonOption, console, emit_json, emit_table, unwrap

app = typer.Typer(no_args_is_help=True, help="Browse and preview sounds.")


def _sound_row(sound: SoundRead) -> dict[str, object]:
    return {"id": str(sound.id), "name": sound.name, "category": sound.category.value}


@app.command("list")
def list_sounds(
    category: Annotated[
        SoundCategory | None, typer.Option(help="Filter by sound category.")
    ] = None,
    json_: JsonOption = False,
) -> None:
    """List the sounds available to alarm profiles."""
    with api_client(Config.from_env()) as client:
        sounds = unwrap(list_sounds_api.sync_detailed(client=client, category=category))

    if json_:
        emit_json([sound.to_dict() for sound in sounds])
    else:
        emit_table(
            [_sound_row(sound) for sound in sounds], empty_message="No sounds found."
        )


@app.command("preview")
def preview_sound(
    sound_id: UUID,
    volume: Annotated[int, typer.Option(min=0, max=100)] = 60,
    json_: JsonOption = False,
) -> None:
    """Start playback of a sound. It keeps playing until you stop it."""
    with api_client(Config.from_env()) as client:
        sound = unwrap(
            preview_sound_api.sync_detailed(
                client=client,
                body=SoundPreviewRequest(sound_id=sound_id, volume=volume),
            )
        )

    if json_:
        emit_json(sound.to_dict())
    else:
        console.print(f"[green]Previewing '{sound.name}' at volume {volume}.[/green]")


@app.command("stop")
def stop_playback() -> None:
    """Stop whatever is currently playing."""
    with api_client(Config.from_env()) as client:
        unwrap(stop_playback_api.sync_detailed(client=client))
    console.print("[green]Stopped.[/green]")


@app.command("volume")
def set_volume(volume: Annotated[int, typer.Argument(min=0, max=100)]) -> None:
    """Set the playback volume."""
    with api_client(Config.from_env()) as client:
        unwrap(
            set_volume_api.sync_detailed(
                client=client, body=VolumeRequest(volume=volume)
            )
        )
    console.print(f"[green]Volume set to {volume}.[/green]")
