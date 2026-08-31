# CLI contract

The `huerise` CLI serves interactive terminal use and reliable automation from
the same command tree.

## Command tree

```text
huerise
├── start
├── stop
├── rooms
├── scenes
├── bridge
│   ├── list
│   ├── status
│   ├── select
│   └── register
├── doctor
└── version
```

Run `huerise --help` or `huerise <command> --help` for arguments, flags, and
defaults.

## Authentication

Every route requires the server's API key, sent as the `X-API-Key` header. Set
`HUERISE_API_KEY` in the environment or the `--env-file` dotenv file, or pass
`--api-key` explicitly.

## Running the alarm

`huerise start` runs the daylight alarm with the duration from the server's
YAML configuration; `--duration-seconds` overrides it for a single run.
`huerise stop` cuts a running alarm short.

`huerise start --watch` additionally follows the fade on one redrawn line
until it finishes. The bar is derived from the duration the server reports, so
watching costs no further requests. Leaving the watch -- Ctrl-C, or closing the
terminal -- does not stop the alarm; only `huerise stop` does. `--watch` is
interactive output and is refused together with `--json` or `--fields`.

## Configuring the alarm

`huerise configuration show` prints the saved room, scene, and duration.

`huerise configuration set <room-id> <scene-id>` saves a configuration without
asking anything, and is the form to use in scripts and from agents. Run
`huerise configuration set` with no IDs and it asks instead: room, scene,
duration in minutes, then a summary to confirm. The fade always starts at 1%
and ends at the brightness stored in the selected scene. Declining the summary
saves nothing and exits `0`.

The questions are skipped whenever answering them would be wrong: with
`--json` or `--fields` the missing IDs are a usage error, and a closed stdin
ends the same way, naming the non-interactive form in the hint. Passing only
one of the two IDs is also a usage error.

## Hue setup and diagnostics

`huerise bridge list` discovers bridges, and `huerise bridge select
<bridge-id>` persists the selected bridge. Press its physical link button, then
run `huerise bridge register`; registration may take up to 60 seconds.
`huerise bridge status` shows the onboarding state of the effective bridge.
`huerise doctor` reports the configuration checks the server runs.

## Human output

Without `--json`, results are printed as an indented table or field list, and
onboarding commands end with a `Next` block naming the command that follows.
Empty results say why they are empty instead of printing a bare table header.
None of this appears in JSON mode.

## Streams and JSON

- stdout contains only result data, plus the `Next` guidance in human mode.
- stderr receives hints and errors.
- `--json` emits one valid JSON document.
- `--compact` removes JSON indentation.
- `--fields=a,b` implies JSON and selects top-level fields from an object or
  every object in a list.
- Unknown fields fail before emitting data and list the available names.

```bash
huerise rooms --fields=id,name --compact
huerise start --duration-seconds=600 --json --compact
```

## Errors and exit codes

Human-readable errors use `Error:` and an optional `Hint:` on stderr. In JSON
mode the same failure is a single object:

```json
{
  "error": {
    "code": "auth",
    "message": "Invalid API key",
    "hint": "Check HUERISE_API_KEY, or pass --api-key.",
    "status": 401
  }
}
```

| Code | Meaning |
| ---: | --- |
| `0` | Success |
| `1` | Transport, API, or local I/O failure |
| `2` | Invalid arguments, missing configuration, or invalid server YAML |
| `3` | Authentication or authorization failure |

A `configuration` error means the server rejected the request because its YAML
is missing or invalid; `hint` then lists the offending locations.

## Configuration precedence

The server URL is resolved in this order:

1. Explicit `--api-url` override
2. `HUERISE_API_URL` environment variable
3. The file selected by `--env-file` (default `.env`)
4. `http://localhost:<HUERISE_PORT>` from the environment or dotenv file
5. The default API URL `http://localhost:8000`

The API key is resolved in this order:

1. Explicit `--api-key` override
2. `HUERISE_API_KEY` environment variable
3. The file selected by `--env-file` (default `.env`)
