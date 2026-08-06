# Hue selection and onboarding

Hue setup will follow the Sonos selection work, but it must support an
unconfigured first start rather than requiring `HUE_BRIDGE_IP` and
`HUE_APP_KEY` during dependency construction.

## Intended flow

1. Discover available bridges and expose their bridge IDs and current IP
   addresses through a setup endpoint.
2. Let the user select a bridge by its stable bridge ID.
3. Ask the user to press the bridge link button and register an application
   key through `hueify.onboarding.register_app_key`.
4. Persist the bridge ID and application key. Treat the discovered IP address
   as replaceable connection metadata rather than device identity.
5. Re-resolve the address during startup or reconnection so DHCP changes do
   not require user configuration.

## Architectural constraint

The current app-scoped `Hueify` dependency and the Hue event-driven lifecycle
require credentials at application startup. Before adding setup routes, these
must be replaced by a configurable Hue connection that can report an
unconfigured state. Hue-dependent operations should then fail with a clear
service-unavailable response without preventing the setup API from starting.

The existing environment variables remain useful as an operator-controlled
bootstrap or deployment override:

- `HUE_BRIDGE_IP`
- `HUE_APP_KEY`

API responses must never return the application key. The later persistence
design must also define whether environment values override stored values or
only seed an empty installation.
