import typer

from huerise_cli.client import api_client
from huerise_cli.config import Config
from huerise_cli.generated.api.audio_output import (
    get_audio_output as get_audio_output_api,
)
from huerise_cli.generated.api.audio_output import (
    select_audio_output as select_audio_output_api,
)
from huerise_cli.generated.models import (
    AudioOutput,
    AudioOutputRead,
    AudioOutputRequest,
)
from huerise_cli.output import JsonOption, console, emit_json, emit_record, unwrap

app = typer.Typer(no_args_is_help=True, help="Switch where audio is played.")


def _render(status: AudioOutputRead, as_json: bool) -> None:
    if as_json:
        emit_json(status.to_dict())
    else:
        emit_record(
            {
                "active": status.active.value,
                "available": ", ".join(output.value for output in status.available),
            }
        )


@app.command("get")
def get_audio_output(json_: JsonOption = False) -> None:
    """Show the current playback output and what's available."""
    with api_client(Config.from_env()) as client:
        status = unwrap(get_audio_output_api.sync_detailed(client=client))
    _render(status, json_)


@app.command("select")
def select_audio_output(output: AudioOutput, json_: JsonOption = False) -> None:
    """Switch playback to a different output. Stops anything currently playing."""
    with api_client(Config.from_env()) as client:
        status = unwrap(
            select_audio_output_api.sync_detailed(
                client=client, body=AudioOutputRequest(output=output)
            )
        )
    _render(status, json_)
    console.print(f"[green]Switched to {output.value}.[/green]")
