# Huerise

Sunrise alarm clock powered by Philips Hue. Gradually increases light brightness to simulate a sunrise, plays an intro ambient sound, then switches to a ringtone — all controlled via a REST API.

## Features

- **Sunrise simulation** — ramps Hue lights from dim to bright over a configurable duration
- **Audio playback** — intro ambient sound during sunrise, followed by a ringtone alarm
- **One-time & recurring alarms** — schedule single alarms or recurring series on specific weekdays
- **Alarm lifecycle** — activate, deactivate, cancel, and delete alarms through the API
- **Sound & scene browsing** — list the available sounds and Hue scenes and preview them before putting them into a profile
- **Configurable audio output** — install local playback, Sonos playback, or both

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
| DELETE | `/alarm-profiles/{profile_id}` | Delete an alarm profile |

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
Sonos speaker on the same network (`sonos`). `AUDIO_BACKENDS` controls which
optional backends exist:

```dotenv
AUDIO_BACKENDS=local       # only local playback
AUDIO_BACKENDS=sonos       # only Sonos playback
AUDIO_BACKENDS=all         # both, switchable at runtime
AUDIO_DEFAULT_OUTPUT=local # initial output when both exist
```

Both alarms and previews follow the active output. Switching stops whatever is
currently playing. Selecting a backend that was not configured returns a
readable `503 Audio output unavailable` response.

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

The selection lives in memory. With both backends configured, a restart falls
back to `AUDIO_DEFAULT_OUTPUT`; a single backend selects itself.

For local ALSA playback on a Linux Docker host, pass `/dev/snd` through with
the optional Compose override:

```bash
docker compose -f compose.yml -f compose.audio.yml up --build
```

The regular `docker compose up --build` remains portable and is also the right
choice when using Sonos. Docker Desktop on Windows and macOS cannot pass host
audio through the Linux `/dev/snd` mapping.

#### Sonos setup

A Sonos speaker streams the sound itself instead of receiving audio from the
API, so it needs two things:

```
SONOS_SPEAKER_NAME=Sonos Era 100
SONOS_IP_ADDRESS=192.168.178.68
MINIO_PUBLIC_ENDPOINT_URL=http://192.168.1.5:9000
```

- `SONOS_SPEAKER_NAME` — the speaker to play on. Left empty, discovery picks
  the first group coordinator it finds.
- `SONOS_IP_ADDRESS` — connects directly and skips SSDP discovery. This is the
  recommended setting when Huerise runs in Docker, where multicast discovery
  may not reach the local network.
- `MINIO_PUBLIC_ENDPOINT_URL` — the address the **speaker** reaches MinIO
  under. Sounds are handed over as presigned links, and a link is only valid
  for the host it was signed for, so `localhost` does not work here.

The Sonos client is connected during application startup, so invalid speaker
configuration and discovery failures fail fast. A local-only process neither
imports `sonosify` nor touches the network.

## Go CLI

The repository includes a typed, script-friendly Go CLI generated from the
API's OpenAPI specification. It follows the same command and output conventions
as [`go-withings`](https://github.com/mathisarends/go-withings): readable tables
by default, stable JSON for automation, clean stdout, and actionable errors on
stderr.

Build it with Go 1.25 or newer:

```bash
make build
./bin/huerise --help
```

On Windows without `make`:

```powershell
go -C cli build -o ../bin/huerise.exe ./cmd/huerise
```

The CLI reads `.env` by default. It uses `HUERISE_API_TOKEN`, falling back to
the backend's `API_ACCESS_TOKEN`, and connects to `http://localhost:8000` unless
`HUERISE_API_URL` is set.

```bash
huerise alarms list
huerise alarms list --json --compact
huerise alarms create "Weekday sunrise" --room Bedroom --hour 7 --minute 0 \
  --day mon --day tue --day wed --day thu --day fri
huerise rooms get Bedroom
huerise sounds list --fields=id,name --compact
huerise audio-output select sonos
```

All data commands support `--json`, `--compact`, and `--fields`. Pass
`--no-input` for unattended use; destructive commands then fail unless their
explicit confirmation flag is present. See [docs/cli.md](docs/cli.md) for the
complete command tree and scripting contract.

### Regenerating the Go client

The Go CLI lives in its own module under [`cli/`](cli/), isolated from the
Python backend. The files in `cli/internal/client/` are generated by
[`ogen`](https://github.com/ogen-go/ogen) from the checked-in `openapi.json`.
After changing a FastAPI route or schema, regenerate and verify the client:

```bash
make generate
make check-generated
```

Do not edit files in `cli/internal/client/` by hand.

## Local Development

Requires [uv](https://docs.astral.sh/uv/) and Python 3.14+. Install only the
backend you use, or both for runtime switching:

```bash
uv sync --extra local
uv sync --extra sonos
uv sync --all-extras
uv run python -m huerise.main
```

Run tests:

```bash
uv run --all-extras pytest
go -C cli test ./...
go -C cli vet ./...
```
