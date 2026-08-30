# Huerise

Huerise runs one YAML-configured daylight alarm on a Philips Hue Bridge. It has
no database, users, schedules, alarm profiles, history, or recovery state.

## Configuration

Copy the examples:

```bash
cp .env.example .env
mkdir -p data
cp huerise.example.yml data/huerise.yml
```

Set a private API key in `.env`:

```dotenv
HUERISE_API_KEY=replace-with-a-long-random-key
HUERISE_LOG_LEVEL=INFO
```

The alarm is fully described by `data/huerise.yml`:

```yaml
daylight_alarm:
  scene_id: "00000000-0000-0000-0000-000000000000"
  start_brightness: 1
  end_brightness: 100
  duration_seconds: 1800
```

Hue onboarding writes the selected bridge and application key into the optional
`hue` section of the same file. As a read-only deployment alternative, set
`HUE_BRIDGE_IP` and `HUE_APP_KEY` together in `.env`.

The YAML file is read on every alarm start and Doctor check. A running alarm
continues with the snapshot it started with.

## Run with Docker

```bash
docker compose up --build -d
```

The API and Swagger UI are available at `http://localhost:8000` and
`http://localhost:8000/docs`. Compose mounts `./data` at `/config`; this YAML
file is the application's only persistent storage.

## API

Send the configured key as `X-API-Key` on every route.

| Method | Route | Purpose |
| --- | --- | --- |
| `GET` | `/doctor` | Validate YAML, credentials, Bridge access, and configured scene |
| `POST` | `/daylight-alarm/start` | Start immediately, optionally overriding this run's duration |
| `POST` | `/daylight-alarm/stop` | Stop it without changing the current light state |
| `GET` | `/rooms` | List Hue rooms and scenes |
| `GET` | `/scenes` | List all scenes with their room |
| `GET` | `/hue/bridges` | Discover Hue Bridges |
| `GET` | `/hue/bridge` | Read onboarding state |
| `PUT` | `/hue/bridge` | Select a discovered Bridge |
| `POST` | `/hue/bridge/register` | Register after pressing the Bridge link button |

The onboarding states are `not_selected`, `link_button_required`, and `ready`.
Registration waits up to 60 seconds for the physical link button. Environment
credentials report `ready` with `read_only: true`.

Example:

```bash
curl -X POST http://localhost:8000/daylight-alarm/start \
  -H "X-API-Key: $HUERISE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"duration_seconds": 10}'
```

Omit the body to use the configured duration. The request may override only the
duration of that run; scene and brightness always come from YAML. Only one run
can be active. A second start returns `409 Conflict`. Stopping is idempotent and
never sends a final Hue command.

## Local development

Huerise requires Python 3.14 and
[`uv`](https://docs.astral.sh/uv/).

```bash
uv sync
$env:HUERISE_API_KEY = "development-key"  # PowerShell
uv run python -m huerise.main
```

Quality checks:

```bash
uv run ruff check .
uv run ruff format --check .
uv run pytest
```

The implementation is split into the `daylight_alarm` and `lighting` features.
Dishka owns their app-scoped services and Hue adapters. The full design scope is
documented in [`HUERISE_CONCEPT_CHANGE.md`](HUERISE_CONCEPT_CHANGE.md).
