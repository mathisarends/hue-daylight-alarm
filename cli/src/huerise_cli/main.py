import sys

import httpx
import typer

from huerise_cli.commands import alarms, audio_output, profiles, rooms, sounds
from huerise_cli.config import ConfigError
from huerise_cli.output import error_console

app = typer.Typer(
    name="huerise",
    help="Command-line client for the Huerise Alarm API.",
    no_args_is_help=True,
)

app.add_typer(alarms.app, name="alarms")
app.add_typer(profiles.app, name="profiles")
app.add_typer(rooms.app, name="rooms")
app.add_typer(sounds.app, name="sounds")
app.add_typer(audio_output.app, name="audio-output")


def main() -> None:
    try:
        app()
    except ConfigError as error:
        error_console.print(f"[bold red]{error}[/bold red]")
        sys.exit(1)
    except httpx.HTTPError as error:
        error_console.print(f"[bold red]Could not reach the API:[/bold red] {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
