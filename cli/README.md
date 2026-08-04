# huerise-cli

Command-line client for the [Huerise](../README.md) Alarm API. Every command
supports `--json` for machine-readable output, so it works equally well for
humans in a terminal and for agents scripting against it.

## Setup

```bash
export HUERISE_API_TOKEN=your-api-access-token   # same value as the server's API_ACCESS_TOKEN
export HUERISE_API_URL=http://localhost:8000     # default, override for a remote server
```

## Usage

```bash
uv run huerise --help
uv run huerise alarms list
uv run huerise alarms list --json
uv run huerise alarms create "Weekday sunrise" --room "Bedroom" \
  --hour 7 --minute 0 --day mon --day tue --day wed --day thu --day fri
```

## Regenerating the API client

`src/huerise_cli/generated/` is produced from the API's own OpenAPI schema
via [openapi-python-client](https://github.com/openapi-generators/openapi-python-client)
and checked in. It is not hand-edited. After changing a router or schema in
`huerise/`, regenerate it from the repo root:

```bash
./scripts/generate_cli_client.sh
```
