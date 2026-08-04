# Huerise

Sunrise alarm clock powered by Philips Hue. Gradually increases light brightness to simulate a sunrise, plays an intro ambient sound, then switches to a ringtone — all controlled via a REST API.

## Features

- **Sunrise simulation** — ramps Hue lights from dim to bright over a configurable duration
- **Audio playback** — intro ambient sound during sunrise, followed by a ringtone alarm
- **One-time & recurring alarms** — schedule single alarms or recurring series on specific weekdays
- **Alarm lifecycle** — activate, deactivate, cancel, and delete alarms through the API
- **Sound & scene browsing** — list the available sounds and Hue scenes and preview them before putting them into a profile
- **Switchable audio output** — play through the local sound device or a Sonos speaker on the network, switched at runtime

## Tech Stack

Python 3.13+ · FastAPI · SQLite (aiosqlite) · SQLModel · Alembic · Dishka (DI) · [hueify](https://pypi.org/project/hueify/) ·
[sonosify](https://pypi.org/project/sonosify/) · uv

## Prerequisites

- Docker & Docker Compose
- A Philips Hue Bridge on your local network
- A Hue API app key ([how to get one](https://developers.meethue.com/develop/get-started-2/))

## Setup

1. **Configure environment variables**

   ```bash
   cp .env.example .env
   ```

   Edit `.env` and fill in your values:

   ```
   API_ACCESS_TOKEN=your-api-access-token
   HUE_APP_KEY=your-hue-app-key
   HUE_BRIDGE_IP=your-hue-bridge-ip
   ```

   `API_ACCESS_TOKEN` is required — the app refuses to start without it.
   Generate one with:

   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

2. **Start the stack**

   ```bash
   docker compose up -d
   ```

   This will:
   - Run database migrations (Alembic)
   - Start the API server on **port 8000**
   - Start Adminer (DB browser) on **port 8080**
   - Start MinIO on **port 9000** and its Console on **port 9001**
   - Create the asset bucket and upload the bundled alarm sounds

   Sign in to the MinIO Console at `http://localhost:9001` with the
   `MINIO_ACCESS_KEY` and `MINIO_SECRET_KEY` values from `.env`.

   To upload the local assets again after changing them:

   ```bash
   ./scripts/upload_assets.sh
   ```

   The files in `assets/` are only seeds for MinIO. Runtime audio playback
   always reads the selected object through the configured storage backend.

3. **Verify**

   ```bash
   curl -H "Authorization: Bearer $API_ACCESS_TOKEN" http://localhost:8000/alarms
   ```

## API

### Authentication

Every endpoint is protected by a single static access token — there are no user
accounts. Send it as a bearer token:

```bash
curl -H "Authorization: Bearer $API_ACCESS_TOKEN" http://localhost:8000/alarms
```

Requests with a missing, malformed, or wrong token get `401 Unauthorized` with a
`WWW-Authenticate: Bearer` header.

Interactive docs are available at `http://localhost:8000/docs` (Swagger UI) —
click **Authorize** and paste the token to call endpoints from there.

### Alarms

| Method | Path                               | Description                         |
| ------ | ---------------------------------- | ----------------------------------- |
| GET    | `/alarms`                          | List all alarms                     |
| POST   | `/alarms`                          | Create an alarm                     |
| GET    | `/alarms/{alarm_id}`               | Get an alarm                        |
| POST   | `/alarms/{alarm_id}/enable`        | Enable an alarm                     |
| POST   | `/alarms/{alarm_id}/disable`       | Disable an alarm                    |
| POST   | `/alarms/{alarm_id}/snooze`        | Snooze an alarm occurrence          |
| POST   | `/alarms/{alarm_id}/dismiss`       | Dismiss an alarm occurrence         |
| GET    | `/alarms/{alarm_id}/occurrences`   | List recent alarm occurrences       |
| DELETE | `/alarms/{alarm_id}`               | Delete an alarm                     |

### Alarm profiles

| Method | Path              | Description              |
| ------ | ----------------- | ------------------------ |
| GET    | `/alarm-profiles` | List all alarm profiles  |
| POST   | `/alarm-profiles` | Create an alarm profile  |

### Rooms and scenes

| Method | Path                                                   | Description                         |
| ------ | ------------------------------------------------------ | ----------------------------------- |
| GET    | `/rooms`                                               | List all Hue rooms                  |
| GET    | `/rooms/{room_name}`                                   | Get a Hue room and its scenes       |
| POST   | `/rooms/{room_name}/scenes/{scene_name}/activate`     | Activate a scene                    |

### Sounds

| Method | Path              | Description                              |
| ------ | ----------------- | ---------------------------------------- |
| GET    | `/sounds`         | List available sounds, optionally filtered by category |
| POST   | `/sounds/preview` | Preview a sound                           |
| POST   | `/sounds/stop`    | Stop the current sound                    |
| POST   | `/sounds/volume`  | Set playback volume                       |

### Audio output

Sounds play either through the machine running the API (`local`) or through a
Sonos speaker on the same network (`sonos`). Both alarms and previews follow
the selected output, and switching stops whatever is currently playing.

| Method | Path             | Description                          |
| ------ | ---------------- | ------------------------------------ |
| GET    | `/audio-output`  | Show the active output               |
| PUT    | `/audio-output`  | Switch the output                    |

```bash
curl -X PUT http://localhost:8000/audio-output \
  -H "Authorization: Bearer $API_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"output": "sonos"}'
```

The selection lives in memory: a restart falls back to `AUDIO_DEFAULT_OUTPUT`
(default `local`).

#### Sonos setup

A Sonos speaker streams the sound itself instead of receiving audio from the
API, so it needs two things:

```
SONOS_ROOM_NAME=Bedroom
MINIO_PUBLIC_ENDPOINT_URL=http://192.168.1.5:9000
```

- `SONOS_ROOM_NAME` — the speaker to play on. Left empty, discovery picks the
  first group coordinator it finds. Set `SONOS_IP` instead if your network
  swallows the SSDP multicast that discovery relies on.
- `MINIO_PUBLIC_ENDPOINT_URL` — the address the **speaker** reaches MinIO
  under. Sounds are handed over as presigned links, and a link is only valid
  for the host it was signed for, so `localhost` does not work here.

Discovery happens on the first playback, not at startup — running with the
local output never touches the network. When the speaker cannot be reached,
the affected request answers `503`.

## CLI

`cli/` is a typed command-line client for the API, built for humans and
agents alike: every command supports `--json` for machine-readable output,
alongside readable tables by default.

```bash
export HUERISE_API_TOKEN=$API_ACCESS_TOKEN   # same value as the server's
export HUERISE_API_URL=http://localhost:8000 # defaults to this

uv run huerise alarms list
uv run huerise alarms create "Weekday sunrise" --room "Bedroom" \
  --hour 7 --minute 0 --day mon --day tue --day wed --day thu --day fri
uv run huerise sounds list --json
```

Run `uv run huerise --help` for the full command tree.

The CLI's types (`cli/src/huerise_cli/generated/`) are generated from the
API's own OpenAPI schema, not hand-maintained. After changing a router or
schema, regenerate them with:

```bash
./scripts/generate_cli_client.sh
```

## Local Development

Requires [uv](https://docs.astral.sh/uv/) and Python 3.14+. The repo is a uv
workspace — `huerise` (the API) and `huerise-cli` (the CLI, in `cli/`) share
one lockfile and virtualenv.

```bash
uv sync
uv run python -m huerise.main
```

Run tests:

```bash
uv run pytest
```
