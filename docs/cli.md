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
├── hue
│   └── bridge
│       ├── list
│       ├── status
│       ├── select
│       └── register
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

## Hue setup and diagnostics

`huerise hue bridge list` discovers bridges, and `huerise hue bridge select
<bridge-id>` persists the selected bridge. Press its physical link button, then
run `huerise hue bridge register`; registration may take up to 60 seconds.
`huerise hue bridge status` shows the onboarding state of the effective bridge.
`huerise doctor` reports the configuration checks the server runs.

## Streams and JSON

- stdout contains only result data.
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
4. The default API URL `http://localhost:8000`

The API key is resolved in this order:

1. Explicit `--api-key` override
2. `HUERISE_API_KEY` environment variable
3. The file selected by `--env-file` (default `.env`)
