# Huerise

Sunrise alarm clock powered by Philips Hue. Gradually increases light brightness to simulate a sunrise, plays an intro ambient sound, then switches to a ringtone — all controlled via a REST API.

## Features

- **Sunrise simulation** — ramps Hue lights from dim to bright over a configurable duration
- **Audio playback** — intro ambient sound during sunrise, followed by a ringtone alarm
- **One-time & recurring alarms** — schedule single alarms or recurring series on specific weekdays
- **Alarm lifecycle** — activate, deactivate, cancel, and delete alarms through the API

## Tech Stack

Python 3.13+ · FastAPI · SQLite (aiosqlite) · SQLModel · Alembic · Dishka (DI) · [hueify](https://pypi.org/project/hueify/) · uv

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
   HUE_APP_KEY=your-hue-app-key
   HUE_BRIDGE_IP=your-hue-bridge-ip
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
   curl http://localhost:8000/alarms
   ```

## API

Interactive docs are available at `http://localhost:8000/docs` (Swagger UI).

Key endpoints:

| Method | Path                      | Description                     |
| ------ | ------------------------- | ------------------------------- |
| GET    | `/alarms`                 | List all alarms                 |
| POST   | `/alarms/one-time`        | Create a one-time alarm         |
| POST   | `/alarms/recurring`       | Create a recurring alarm series |
| POST   | `/alarms/{id}/activate`   | Activate an alarm               |
| POST   | `/alarms/{id}/deactivate` | Deactivate an alarm             |
| POST   | `/alarms/{id}/cancel`     | Cancel a running alarm          |
| DELETE | `/alarms/{id}`            | Delete an alarm                 |
| DELETE | `/alarms/series/{id}`     | Delete a recurring series       |

## Local Development

Requires [uv](https://docs.astral.sh/uv/) and Python 3.14+.

```bash
uv sync
uv run python -m huerise.main
```

Run tests:

```bash
uv run pytest
```
