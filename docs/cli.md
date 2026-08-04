# CLI contract

The `huerise` CLI serves interactive terminal use and reliable automation from
the same command tree.

## Command tree

```text
huerise
├── alarms
│   ├── list
│   ├── create
│   ├── get
│   ├── enable
│   ├── disable
│   ├── snooze
│   ├── dismiss
│   ├── occurrences
│   └── delete
├── profiles
│   ├── list
│   ├── create
│   └── delete
├── rooms
│   ├── list
│   ├── get
│   └── activate-scene
├── sounds
│   ├── list
│   ├── preview
│   ├── stop
│   └── volume
├── audio-output
│   ├── get
│   └── select
└── version
```

Run `huerise --help` or `huerise <command> --help` for arguments, flags, and
defaults.

## Streams and JSON

- stdout contains only result data.
- stderr receives prompts, hints, and errors.
- `--json` emits one valid JSON document and never prompts.
- `--compact` removes JSON indentation.
- `--fields=a,b` implies JSON and selects top-level fields from an object or
  every object in a list.
- Unknown fields fail before emitting data and list the available names.

For unattended calls, pass `--no-input`. Alarm and profile deletion require
`--yes`; this keeps agents and scripts from blocking on or bypassing a prompt by
accident.

```bash
huerise --no-input alarms list --fields=id,label,next_occurrence --compact
huerise --no-input alarms delete ALARM_ID --yes --json --compact
```

## Errors and exit codes

Human-readable errors use `Error:` and an optional `Hint:` on stderr. In JSON
mode the same failure is a single object:

```json
{
  "error": {
    "code": "auth",
    "message": "Invalid access token",
    "hint": "Check HUERISE_API_TOKEN and try again.",
    "status": 401
  }
}
```

| Code | Meaning |
| ---: | --- |
| `0` | Success |
| `1` | Transport, API, cancellation, or local I/O failure |
| `2` | Invalid arguments, missing configuration, or required input |
| `3` | Authentication or authorization failure |

## Configuration precedence

Configuration is resolved in this order:

1. Explicit `--api-url` and hidden `--token` overrides
2. Environment variables
3. The file selected by `--env-file` (default `.env`)
4. The default API URL `http://localhost:8000`

`HUERISE_API_TOKEN` falls back to `API_ACCESS_TOKEN`, allowing the backend and
CLI to share one local `.env` file. `HUERISE_API_URL` selects a remote backend.
