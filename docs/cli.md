# CLI contract

The `huerise` CLI serves interactive terminal use and reliable automation from
the same command tree.

## Command tree

```text
huerise
├── auth
│   ├── register
│   ├── login
│   └── logout
├── alarms
│   ├── list
│   ├── create
│   ├── get
│   ├── enable
│   ├── disable
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
│   ├── activate-scene
│   ├── demo
│   └── stop-demo
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

`huerise auth register --username <name>` creates the first account on a
fresh install; `huerise auth login --username <name>` authenticates on any
later machine. Both prompt for a password if `--password` is omitted and the
terminal is interactive; pass `--no-input` to require flags instead. The
resulting access/refresh token pair is stored per-machine at
`~/.huerise/credentials.json` and used automatically by every other command
— the access token refreshes transparently as it nears expiry. `huerise auth
logout` revokes the refresh token server-side and forgets the local file.

## Hue setup and diagnostics

`huerise hue bridge list` discovers bridges, and `huerise hue bridge select
<bridge-id>` persists the selected bridge. Press its physical link button, then
run `huerise hue bridge register`; registration may take up to 60 seconds.
`huerise hue bridge status` shows the effective bridge configuration and its
source. `huerise doctor` reports whether the Hue Bridge is configured.

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
    "hint": "Run `huerise auth login`, or check HUERISE_API_TOKEN.",
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

The server URL is resolved in this order:

1. Explicit `--api-url` override
2. `HUERISE_API_URL` environment variable
3. The file selected by `--env-file` (default `.env`)
4. The default API URL `http://localhost:8000`

Authentication is resolved in this order:

1. Explicit hidden `--token` override
2. `HUERISE_API_TOKEN` environment variable or `--env-file` entry
3. The credentials `huerise auth login`/`auth register` stored at
   `~/.huerise/credentials.json`, refreshed automatically as they expire

Run `huerise auth logout` to revoke and forget stored credentials.
