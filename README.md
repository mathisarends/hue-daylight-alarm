# Huerise

Huerise wakes you up with light. It drives a Philips Hue Bridge through a
gradual sunrise: the configured scene comes up at its dimmest, then brightens
smoothly to the brightness stored in that scene over the duration you choose.

A single YAML file describes the alarm, and an HTTP API plus a `huerise` CLI
start it, stop it, and check that everything is wired up. Scheduling stays with
whatever already runs on time for you — cron, a home automation system, a phone
shortcut — which calls `POST /daylight-alarm/start`.

## How it works

Starting an alarm runs one linear brightness ramp:

1. The YAML file is read fresh, so the latest configuration always applies.
2. The room owning `scene_id` is resolved from the Bridge.
3. The scene is activated at 1% brightness, setting its colors at their
   dimmest.
4. A background task then steps the room's brightness once per second, moving
   linearly from 1% to the brightness stored in the scene across
   `duration_seconds`.
5. When the ramp completes the lights simply stay where they are. Huerise sends
   no final command and never switches anything off.

Because the configuration is read at start time, a running alarm keeps the
snapshot it began with; editing the YAML mid-run affects only the next one.
Exactly one alarm can be active at a time, and `stop` cancels the ramp in place
— the lights hold their current brightness rather than jumping back.

`GET /doctor` runs the same preconditions ahead of time: the YAML parses and
validates, Hue credentials exist, the Bridge answers and accepts them, and the
configured scene still exists.

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
HUERISE_PORT=8000
```

`HUERISE_PORT` controls the port published on the host. The application keeps
listening on port 8000 inside the container.

The alarm is fully described by `data/huerise.yml`:

```yaml
daylight_alarm:
  room:
    id: "00000000-0000-0000-0000-000000000000"
    name: Bedroom
  scene:
    id: "00000000-0000-0000-0000-000000000000"
    name: Sunrise
  duration_seconds: 1800
  after_alarm:
    room:
      id: "00000000-0000-0000-0000-000000000000"
      name: Bedroom
    scene:
      id: "00000000-0000-0000-0000-000000000000"
      name: Evening
    delay_seconds: 600
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

With the default `HUERISE_PORT`, the API and Swagger UI are available at
`http://localhost:8000` and `http://localhost:8000/docs`. Compose mounts
`./data` at `/config`; this YAML file is the application's only persistent
storage.

## API

Send the configured key as `X-API-Key` on every route.

| Method | Route | Purpose |
| --- | --- | --- |
| `GET` | `/doctor` | Validate YAML, credentials, Bridge access, and configured scene |
| `POST` | `/daylight-alarm/start` | Start immediately, optionally overriding this run's duration |
| `POST` | `/daylight-alarm/stop` | Stop it without changing the current light state |
| `GET` | `/daylight-alarm/configuration` | Read the human-readable alarm configuration |
| `PUT` | `/daylight-alarm/configuration` | Save the selected room, scene, and duration |
| `GET` | `/scenes` | List all scenes with their room and reference brightness |
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
duration of that run. The scene comes from YAML, while its target brightness is
read fresh from the Hue Bridge when the alarm starts. A second start while an
alarm is running returns `409 Conflict`, and stopping is idempotent.

## CLI

The `huerise` CLI in [`cli/`](cli) talks to the same API and is documented in
[`docs/cli.md`](docs/cli.md).

```bash
huerise doctor
huerise start --duration-seconds 900
huerise stop
```

It reads `HUERISE_API_URL` and `HUERISE_API_KEY` from the environment or a
dotenv file (`--env-file`). Every command also prints machine-readable output
with `--json`.

When `HUERISE_API_URL` is unset, the CLI connects to localhost using
`HUERISE_PORT`, or port 8000 when neither setting is present. Set the full URL
when the container runs on another host:

```dotenv
HUERISE_API_URL=http://huerise.local:8080
```

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

Releases are built from semantic-version Git tags. See
[`docs/relase.md`](docs/relase.md) for the complete release process.

The implementation is split into the `daylight_alarm` and `lighting` features,
each layered into `application`, `infrastructure`, and `presentation`. Dishka
owns their app-scoped services and Hue adapters.
