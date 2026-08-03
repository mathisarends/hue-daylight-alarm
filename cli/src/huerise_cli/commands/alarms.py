from typing import Annotated
from uuid import UUID

import typer

from huerise_cli.client import api_client
from huerise_cli.config import Config
from huerise_cli.generated.api.alarms import (
    create_alarm as create_alarm_api,
    delete_alarm as delete_alarm_api,
    disable_alarm as disable_alarm_api,
    dismiss_alarm as dismiss_alarm_api,
    enable_alarm as enable_alarm_api,
    get_alarm as get_alarm_api,
    list_alarms as list_alarms_api,
    list_occurrences as list_occurrences_api,
    snooze_alarm as snooze_alarm_api,
)
from huerise_cli.generated.models import (
    AlarmCreate,
    AlarmRead,
    OccurrenceRead,
    ScheduleSchema,
    SnoozeRequest,
    Weekday,
)
from huerise_cli.generated.types import UNSET, Unset
from huerise_cli.output import (
    JsonOption,
    console,
    emit_json,
    emit_record,
    emit_table,
    unwrap,
)

app = typer.Typer(no_args_is_help=True, help="Manage sunrise alarms.")

_WEEKDAYS = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")


def _parse_days(days: list[str]) -> list[Weekday]:
    try:
        return [Weekday(_WEEKDAYS.index(day.lower())) for day in days]
    except ValueError as error:
        raise typer.BadParameter(
            f"{error}. Choose from: {', '.join(_WEEKDAYS)}"
        ) from error


def _format_schedule(schedule: ScheduleSchema) -> str:
    time = f"{schedule.hour:02d}:{schedule.minute:02d}"
    if isinstance(schedule.days, Unset) or not schedule.days:
        return f"{time} once"
    names = ",".join(_WEEKDAYS[int(day)] for day in schedule.days)
    return f"{time} {names}"


def _alarm_row(alarm: AlarmRead) -> dict[str, object]:
    return {
        "id": str(alarm.id),
        "label": alarm.label,
        "room": alarm.room_name,
        "schedule": _format_schedule(alarm.schedule),
        "enabled": alarm.is_enabled,
        "next": alarm.next_occurrence.isoformat() if alarm.next_occurrence else "-",
    }


def _render_alarm(alarm: AlarmRead, as_json: bool) -> None:
    if as_json:
        emit_json(alarm.to_dict())
    else:
        emit_record(_alarm_row(alarm))


def _occurrence_row(occurrence: OccurrenceRead) -> dict[str, object]:
    return {
        "id": str(occurrence.id),
        "scheduled_for": occurrence.scheduled_for.isoformat(),
        "state": occurrence.state,
        "snoozes": occurrence.snooze_count,
        "failure_reason": occurrence.failure_reason or "-",
    }


def _render_occurrence(occurrence: OccurrenceRead, as_json: bool) -> None:
    if as_json:
        emit_json(occurrence.to_dict())
    else:
        emit_record(_occurrence_row(occurrence))


@app.command("list")
def list_alarms(json_: JsonOption = False) -> None:
    """List every alarm."""
    with api_client(Config.from_env()) as client:
        alarms = unwrap(list_alarms_api.sync_detailed(client=client))

    if json_:
        emit_json([alarm.to_dict() for alarm in alarms])
    else:
        emit_table(
            [_alarm_row(alarm) for alarm in alarms], empty_message="No alarms yet."
        )


@app.command("create")
def create_alarm(
    label: Annotated[str, typer.Argument(help="Human-readable name for the alarm.")],
    room: Annotated[str, typer.Option(help="Room to run the sunrise scene in.")],
    hour: Annotated[int, typer.Option(min=0, max=23, help="Hour, 0-23.")],
    minute: Annotated[int, typer.Option(min=0, max=59, help="Minute, 0-59.")],
    timezone: Annotated[str, typer.Option(help="IANA timezone.")] = "Europe/Berlin",
    day: Annotated[
        list[str] | None,
        typer.Option(
            "--day",
            help=f"Weekday to repeat on ({', '.join(_WEEKDAYS)}). "
            "Omit for a one-off alarm.",
        ),
    ] = None,
    profile_id: Annotated[
        UUID | None,
        typer.Option(help="Alarm profile to use. Defaults to the default profile."),
    ] = None,
    json_: JsonOption = False,
) -> None:
    """Create a new alarm."""
    schedule = ScheduleSchema(
        hour=hour, minute=minute, timezone=timezone, days=_parse_days(day or [])
    )
    body = AlarmCreate(
        label=label,
        schedule=schedule,
        room_name=room,
        profile_id=profile_id if profile_id is not None else UNSET,
    )
    with api_client(Config.from_env()) as client:
        alarm = unwrap(create_alarm_api.sync_detailed(client=client, body=body))
    _render_alarm(alarm, json_)


@app.command("get")
def get_alarm(alarm_id: UUID, json_: JsonOption = False) -> None:
    """Show a single alarm."""
    with api_client(Config.from_env()) as client:
        alarm = unwrap(get_alarm_api.sync_detailed(client=client, alarm_id=alarm_id))
    _render_alarm(alarm, json_)


@app.command("enable")
def enable_alarm(alarm_id: UUID, json_: JsonOption = False) -> None:
    """Enable an alarm."""
    with api_client(Config.from_env()) as client:
        alarm = unwrap(enable_alarm_api.sync_detailed(client=client, alarm_id=alarm_id))
    _render_alarm(alarm, json_)


@app.command("disable")
def disable_alarm(alarm_id: UUID, json_: JsonOption = False) -> None:
    """Disable an alarm."""
    with api_client(Config.from_env()) as client:
        alarm = unwrap(
            disable_alarm_api.sync_detailed(client=client, alarm_id=alarm_id)
        )
    _render_alarm(alarm, json_)


@app.command("snooze")
def snooze_alarm(
    alarm_id: UUID,
    minutes: Annotated[int, typer.Option(min=1, max=60)] = 10,
    json_: JsonOption = False,
) -> None:
    """Snooze the alarm's current occurrence."""
    with api_client(Config.from_env()) as client:
        occurrence = unwrap(
            snooze_alarm_api.sync_detailed(
                client=client, alarm_id=alarm_id, body=SnoozeRequest(minutes=minutes)
            )
        )
    _render_occurrence(occurrence, json_)


@app.command("dismiss")
def dismiss_alarm(alarm_id: UUID, json_: JsonOption = False) -> None:
    """Dismiss the alarm's current occurrence."""
    with api_client(Config.from_env()) as client:
        occurrence = unwrap(
            dismiss_alarm_api.sync_detailed(client=client, alarm_id=alarm_id)
        )
    _render_occurrence(occurrence, json_)


@app.command("occurrences")
def list_occurrences(
    alarm_id: UUID,
    limit: Annotated[int, typer.Option(help="Max occurrences to return.")] = 20,
    json_: JsonOption = False,
) -> None:
    """List past and upcoming occurrences of an alarm."""
    with api_client(Config.from_env()) as client:
        occurrences = unwrap(
            list_occurrences_api.sync_detailed(
                client=client, alarm_id=alarm_id, limit=limit
            )
        )
    if json_:
        emit_json([occurrence.to_dict() for occurrence in occurrences])
    else:
        emit_table(
            [_occurrence_row(occurrence) for occurrence in occurrences],
            empty_message="No occurrences yet.",
        )


@app.command("delete")
def delete_alarm(
    alarm_id: UUID,
    yes: Annotated[
        bool, typer.Option("--yes", "-y", help="Skip confirmation.")
    ] = False,
) -> None:
    """Delete an alarm."""
    if not yes:
        typer.confirm(f"Delete alarm {alarm_id}?", abort=True)
    with api_client(Config.from_env()) as client:
        unwrap(delete_alarm_api.sync_detailed(client=client, alarm_id=alarm_id))
    console.print(f"[green]Deleted alarm {alarm_id}.[/green]")
