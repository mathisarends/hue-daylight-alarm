import json
from typing import Annotated, Any, NoReturn

import typer
from rich.console import Console
from rich.table import Table

from huerise_cli.generated.types import Response

console = Console()
error_console = Console(stderr=True)

JsonOption = Annotated[
    bool, typer.Option("--json", help="Output raw JSON instead of a table.")
]


def unwrap[T](response: Response[T]) -> T:
    """Return the parsed body of a 2xx response, or exit with a formatted error."""
    if 200 <= response.status_code < 300:
        return response.parsed  # type: ignore[return-value]
    _fail(response)


def _fail(response: Response[Any]) -> NoReturn:
    error_console.print(
        f"[bold red]Error {response.status_code}:[/bold red] {_detail(response)}"
    )
    raise typer.Exit(code=1)


def _detail(response: Response[Any]) -> str:
    try:
        body = json.loads(response.content)
    except json.JSONDecodeError, UnicodeDecodeError:
        return response.content.decode(errors="replace")

    detail = body.get("detail") if isinstance(body, dict) else None
    if isinstance(detail, str):
        return detail
    return json.dumps(detail if detail is not None else body)


def emit_json(data: Any) -> None:
    console.print_json(data=data)


def emit_table(
    rows: list[dict[str, Any]],
    *,
    columns: list[str] | None = None,
    empty_message: str = "Nothing to show.",
) -> None:
    if not rows:
        console.print(f"[dim]{empty_message}[/dim]")
        return

    columns = columns or list(rows[0].keys())
    table = Table()
    for column in columns:
        table.add_column(column)
    for row in rows:
        table.add_row(*(str(row.get(column, "")) for column in columns))
    console.print(table)


def emit_record(fields: dict[str, Any]) -> None:
    table = Table(show_header=False)
    table.add_column("Field", style="bold")
    table.add_column("Value")
    for key, value in fields.items():
        table.add_row(key, str(value))
    console.print(table)
