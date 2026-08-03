from typing import Annotated
from uuid import UUID

import typer

from huerise_cli.client import api_client
from huerise_cli.config import Config
from huerise_cli.generated.api.alarm_profiles import (
    create_profile as create_profile_api,
)
from huerise_cli.generated.api.alarm_profiles import (
    list_profiles as list_profiles_api,
)
from huerise_cli.generated.models import (
    IntroSchema,
    ProfileCreate,
    ProfileRead,
    RingtoneSchema,
    SunriseSchema,
)
from huerise_cli.output import JsonOption, emit_json, emit_record, emit_table, unwrap

app = typer.Typer(no_args_is_help=True, help="Manage alarm profiles.")


def _profile_row(profile: ProfileRead) -> dict[str, object]:
    return {
        "id": str(profile.id),
        "name": profile.name,
        "default": profile.is_default,
        "scene": profile.sunrise.scene_name,
        "intro_sound": str(profile.intro.sound_id),
        "ringtone_sound": str(profile.ringtone.sound_id),
    }


def _render_profile(profile: ProfileRead, as_json: bool) -> None:
    if as_json:
        emit_json(profile.to_dict())
    else:
        emit_record(_profile_row(profile))


@app.command("list")
def list_profiles(json_: JsonOption = False) -> None:
    """List every alarm profile."""
    with api_client(Config.from_env()) as client:
        profiles = unwrap(list_profiles_api.sync_detailed(client=client))

    if json_:
        emit_json([profile.to_dict() for profile in profiles])
    else:
        emit_table(
            [_profile_row(profile) for profile in profiles],
            empty_message="No profiles yet.",
        )


@app.command("create")
def create_profile(
    name: Annotated[str, typer.Argument(help="Human-readable name for the profile.")],
    intro_sound_id: Annotated[
        UUID, typer.Option(help="Sound id from `huerise sounds list`.")
    ],
    ringtone_sound_id: Annotated[
        UUID, typer.Option(help="Sound id from `huerise sounds list`.")
    ],
    ringtone_volume: Annotated[int, typer.Option(min=0, max=100)] = 80,
    scene_name: Annotated[
        str, typer.Option(help="Hue scene from `huerise rooms get <room>`.")
    ] = "Tageslichtwecker",
    duration_minutes: Annotated[int, typer.Option(min=0, max=120)] = 7,
    brightness_start: Annotated[int, typer.Option(min=1, max=99)] = 1,
    brightness_end: Annotated[int, typer.Option(min=2, max=100)] = 100,
    json_: JsonOption = False,
) -> None:
    """Create a new alarm profile."""
    body = ProfileCreate(
        name=name,
        intro=IntroSchema(sound_id=intro_sound_id),
        ringtone=RingtoneSchema(sound_id=ringtone_sound_id, volume=ringtone_volume),
        sunrise=SunriseSchema(
            scene_name=scene_name,
            duration_minutes=duration_minutes,
            brightness_start=brightness_start,
            brightness_end=brightness_end,
        ),
    )
    with api_client(Config.from_env()) as client:
        profile = unwrap(create_profile_api.sync_detailed(client=client, body=body))
    _render_profile(profile, json_)
