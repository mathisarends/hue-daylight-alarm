# Hue selection and onboarding

Hue setup will follow the Sonos selection work, but it must support an
unconfigured first start rather than requiring `HUE_BRIDGE_IP` and
`HUE_APP_KEY` during dependency construction.

## Implemented flow

1. Discover available bridges and expose their bridge IDs and current IP
   addresses through a setup endpoint.
2. Let the user select a bridge by its stable bridge ID.
3. Ask the user to press the bridge link button and register an application
   key through `hueify.onboarding.register_app_key`.
4. Persist the bridge ID and application key. Treat the discovered IP address
   as replaceable connection metadata rather than device identity.
5. Re-resolve the address during startup or reconnection so DHCP changes do
   not require user configuration.

The backend exposes the onboarding flow through authenticated REST endpoints:

- `GET /hue/bridges` discovers bridges and marks the selected one.
- `PUT /hue/bridge` selects a discovered bridge by stable ID.
- `POST /hue/bridge/register` polls for the bridge link button for up to 60
  seconds, persists the returned application key, and activates Hue without a
  process restart.
- `GET /hue/bridge` reports the effective configuration source and status.
- `GET /doctor` reports Hue Bridge and Sonos speaker configuration separately.

## Architecture

Hue selection has separate domain, application, persistence, adapter, and
presentation layers. The app-scoped configurable Hue runtime can start without
credentials. Hue-dependent operations return `503 Service Unavailable` until
onboarding completes, while setup and non-Hue APIs remain available.

The database stores one selection containing the stable bridge ID, its last
known IP address, and the application key. Startup discovery refreshes the IP
for the stored ID; the last address remains a fallback if discovery is
temporarily unavailable.

The existing environment variables are an operator-controlled deployment
override:

- `HUE_BRIDGE_IP`
- `HUE_APP_KEY`

Both variables must be set together. A complete pair takes precedence over the
stored selection and makes the selection and registration endpoints return a
conflict instead of silently changing an ineffective database value.
Environment values are not copied into the database.

API responses never return the application key.
