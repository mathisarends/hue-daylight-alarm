# Auth, User & Multi-Tenant Support

## Context

Huerise currently authenticates every API request against a single static
bearer token (`huerise/presentation/auth.py`, `API_ACCESS_TOKEN`) — there is
no user concept, and the whole installation is implicitly one tenant. The CLI
(`cli/`) just forwards that same static token from `.env`/env vars.

Two things are being introduced together, deliberately, because the second
depends on the first:

1. **A real identity**: a `user` feature (account + password) and an `auth`
   feature (register/login/refresh/logout, JWT access tokens + opaque
   refresh tokens, argon2id password hashing) replacing the static token.
2. **Multi-tenancy**, per `plans/MULTI_TENANT_SUPPORT.md`: every user's data
   (alarms, profiles, rooms, speakers, events) becomes isolated per tenant,
   enforced centrally in the persistence layer — not opt-in per router.

Decisions already confirmed with the user:
- Password hashing: **argon2-cffi** (new dependency).
- Tokens: **JWT access token** (short-lived, stateless, signed) + **opaque
  refresh token** (long-lived, stored hashed in DB, rotated on use).
- `/auth/register` is a **public** endpoint (no admin gate).
- **v1 tenant model**: no separate `Tenant`/membership table. `tenant_id`
  *is* the registering user's own `id`. This matches the plan doc's own
  "Nicht festgelegt" section (it explicitly allows deferring
  memberships/roles) and avoids building infrastructure nobody needs yet.
  The seam stays clean: every tenant-owned row stores `tenant_id`
  independently of `user_id`, so extracting a real `Tenant` table later is
  additive, not a rewrite.
- Full scope in one plan (not split into a later follow-up): user+auth,
  then the full tenant-isolation migration across data model, repositories,
  scheduler/runner, and event stream.

Work proceeds in the numbered stages below, each its own small commit (per
`CLAUDE.md`), with a checkpoint shown after Stage 2 and Stage 5 in
particular since those are the highest-risk (auth replacement, tenant
enforcement).

## Existing conventions to reuse (don't reinvent)

- **Feature package shape**: `domain/` (entities + abstract `Repository`),
  `application/` (services), `infrastructure/` (`persistence/` SQL repos +
  `di.py` Dishka `Provider`), `presentation/` (routers/schemas). See
  `huerise/features/alarm/` as the template. A feature is wired up via a
  `Feature(...)` object in `<feature>/__init__.py` and registered in
  `huerise/features/__init__.py:FEATURES`.
- **Generic repository base**: `huerise/infrastructure/database/repository.py:11`
  `Repository[ORM: DatabaseEntity, Domain]` — `find_by_id`, `find_by`,
  `find_all`, `save`, `delete_by_id`, `exists`. Concrete repos subclass this
  (e.g. `huerise/features/alarm/infrastructure/persistence/repository.py`).
- **All tables in one module**: `huerise/infrastructure/database/models.py`
  (comment at top explains why — Alembic needs one place with no feature
  imports). New tables go here too.
- **DI**: Dishka `Provider` per feature, `Scope.APP` for singletons,
  `Scope.REQUEST` for per-request services — see
  `huerise/features/alarm/infrastructure/di.py` and
  `huerise/features/devices/infrastructure/di.py`.
- **Auth dependency wiring**: routers attach auth via
  `APIRouter(dependencies=[Depends(require_access_token)])` — e.g.
  `huerise/features/alarm/presentation/alarm_router.py:20`. All 8 routers
  listed in exploration do this identically; the replacement dependency
  slots into the same place.
- **Go client generation**: `make generate` (`Makefile:16`) runs
  `scripts/export_openapi.py` → `openapi.json` → `cli/openapi.json` → ogen
  → `cli/internal/client`. Any new FastAPI endpoint needs this rerun before
  the CLI can call it.
- **CLI config loading**: `cli/internal/huerise/config.go` (`LoadConfig`) —
  read-only today; a login command adds the first *writer*.

## Stage 0 — Write this plan into the repo

Copy this plan to `plans/AUTH_AND_TENANT_SUPPORT.md` (same directory as the
existing `plans/MULTI_TENANT_SUPPORT.md`) so it's trackable in git and
reviewable stage-by-stage as work lands — this is the first commit, before
any code changes.

## Stage 1 — `features/user`

New package `huerise/features/user/` mirroring the `alarm` feature shape:

- `domain/user.py`: `User` entity — `id: UUID`, `username: str`,
  `password_hash: str`, `created_at: datetime`.
- `domain/repository.py`: `UserRepository` ABC — `find_by_id`,
  `find_by_username`, `save`.
- `infrastructure/persistence.py`: `SQLUserRepository(Repository[UserModel, User])`.
- `infrastructure/di.py`: `UserProvider` (`Scope.APP` for the repository,
  matching how `SoundRepository` etc. are provided in the devices feature).
- `application/user_service.py`: `UserService.register(username, password) -> User`
  — hashes via argon2-cffi, rejects duplicate usernames
  (`UserRepository.find_by_username`), no router yet (auth feature owns the
  public endpoint in Stage 2).
- New table in `huerise/infrastructure/database/models.py`:
  `UserModel(DatabaseEntity, table=True)` — `username` unique, `password_hash`,
  `created_at`.
- Alembic migration: `users` table.
- `pyproject.toml`: add `argon2-cffi` (`uv add argon2-cffi`).

**Checkpoint**: migration applies cleanly, `UserService.register` covered by
a unit test with a real (test) DB session, no HTTP surface yet.

## Stage 2 — `features/auth` (replaces the static token)

New package `huerise/features/auth/`:

- `domain/refresh_token.py`: `RefreshToken` entity — `id`, `user_id`,
  `token_hash` (sha256 of the opaque secret — the raw token is never
  stored), `issued_at`, `expires_at`, `revoked_at: datetime | None`.
- New table: `RefreshTokenModel(DatabaseEntity, table=True)`, indexed on
  `token_hash` and `user_id`. Alembic migration.
- `infrastructure/settings.py`: `AuthSettings(BaseSettings)` —
  `jwt_secret: SecretStr` (env `AUTH_JWT_SECRET`), `access_token_ttl_minutes`
  (default 15), `refresh_token_ttl_days` (default 30). Same
  `pydantic-settings` pattern as today's `ApiSettings`.
- `application/auth_service.py`: `AuthService`:
  - `register(username, password) -> TokenPair` — delegates to `UserService`,
    then issues tokens.
  - `login(username, password) -> TokenPair` — argon2 verify; on unknown
    username, still run a dummy argon2 verify against a fixed hash before
    returning 401, so response timing doesn't leak whether the username
    exists.
  - `refresh(refresh_token: str) -> TokenPair` — hash lookup, reject if
    expired/revoked, **rotate**: revoke the presented token, issue a new
    pair. If a *revoked* token is presented again (reuse), revoke every
    active refresh token for that user (stolen-token containment).
  - `logout(refresh_token: str) -> None` — revoke.
  - JWT helper (`infrastructure/jwt.py`): encode `{sub: user_id, tenant_id,
    exp, iat}` with `AuthSettings.jwt_secret`, HS256. New dependency:
    `pyjwt` (`uv add pyjwt`).
- `presentation/auth_router.py` — **no** auth dependency on this router
  (these endpoints establish identity):
  - `POST /auth/register {username, password} -> TokenPair`
  - `POST /auth/login {username, password} -> TokenPair`
  - `POST /auth/refresh {refresh_token} -> TokenPair`
  - `POST /auth/logout {refresh_token} -> 204`
- Replace `huerise/presentation/auth.py`: drop `ApiSettings`/`require_access_token`,
  add `get_current_user` — decodes+verifies the JWT from `Authorization:
  Bearer`, returns `CurrentUser(id: UUID, tenant_id: UUID)` (a plain
  dependency, not Dishka — mirrors today's module-level dependency, no
  DB hit per request since the JWT is self-contained).
- Update all 8 routers (`alarm_router.py`, `profile_router.py`,
  `event_stream_router.py`, `hue_router.py`, `sound_router.py`,
  `doctor_router.py`, `scene_router.py`, `audio_output_router.py`): swap
  `Depends(require_access_token)` → `Depends(get_current_user)`.
- Register `user.feature` and `auth.feature` in `huerise/features/__init__.py:FEATURES`.
- Tests: rewrite `tests/presentation/test_auth.py` for the new dependency
  (register/login/refresh/logout/reuse-detection cases), update
  `tests/conftest.py` (drop the `API_ACCESS_TOKEN` env default, add
  `AUTH_JWT_SECRET` instead).
- `.env.example`: replace `API_ACCESS_TOKEN` with `AUTH_JWT_SECRET`.
- `huerise/app.py:19` description text no longer promises "every endpoint
  requires an Authorization: Bearer token" against a fixed shared secret —
  update wording.

**Checkpoint**: full test suite green, manual `curl` walk-through of
register → login → authenticated request → refresh → logout shown before
moving on — this is the "auth+user Fundament" checkpoint.

## Stage 3 — CLI login

- `cli/internal/commands/`: new `auth.go` with `huerise auth register` and
  `huerise auth login` (prompt for username/password, or flags for
  scripting).
- `cli/internal/huerise/config.go`: add a credentials writer (new file,
  e.g. `credentials.go`) persisting `{access_token, refresh_token,
  expires_at}` to a local file (`~/.huerise/credentials.json` — kept
  separate from the project-local `.env` `LoadConfig` reads today, since
  credentials are per-machine, not per-project).
- `cli/internal/huerise/client.go`: on a 401, transparently call
  `/auth/refresh` with the stored refresh token, retry once, and persist
  the rotated pair — mirrors `bearerToken`'s role in `oas_security_gen.go`
  but now backed by a refreshable pair instead of a static string.
- `make generate` after the new `/auth/*` endpoints exist server-side, to
  regenerate `cli/internal/client` from `openapi.json`.

**Checkpoint**: `huerise auth register` + `huerise auth login` demoed
end-to-end against a local server, token auto-refresh shown by forcing an
access-token expiry.

## Stage 4 — Tenant column on owned data + backfill migration

Per `plans/MULTI_TENANT_SUPPORT.md`, tenant-owned tables get `tenant_id`;
the shared sound catalog does not.

- `huerise/infrastructure/database/models.py`: new abstract
  `TenantEntity(DatabaseEntity)` with `tenant_id: UUID = Field(index=True)`.
  Switch these models to inherit it instead of `DatabaseEntity`:
  `AlarmModel`, `AlarmProfileModel`, `AlarmOccurrenceModel`,
  `SonosSpeakerSelectionModel`, `HueBridgeSelectionModel`. `SoundModel`
  stays as-is (installation-wide catalog, per the plan).
  `SonosSpeakerSelectionModel`/`HueBridgeSelectionModel` also change their
  uniqueness from "one row, ever" (`_SONOS_SELECTION_ID`/`_HUE_SELECTION_ID`
  fixed UUIDs in `huerise/features/devices/infrastructure/persistence.py:21-22`)
  to "one row per tenant" (`unique(tenant_id)`).
- New table: `HueRoomAssignmentModel(DatabaseEntity, table=True)` —
  `tenant_id` (indexed), `room_id` (unique) — persists "which tenant owns
  this Hue room," since rooms themselves are never persisted (they're
  live values from the bridge, per `huerise/features/devices/domain/room.py`).
- Matching domain entities (`Alarm`, `AlarmProfile`, `AlarmOccurrence`,
  the Sonos/Hue selection domain objects) gain a `tenant_id: UUID` field.
- Alembic migration: add the columns, then **backfill** — assign every
  existing row to the tenant_id of the first (or only) registered user,
  per the plan's explicit requirement that an existing single-user install
  keeps working after upgrade. Then make the column non-nullable.

**Checkpoint**: migration runs against a copy of a real `daylight.db`,
schema diff shown, existing rows confirmed backfilled to one tenant.

## Stage 5 — Enforce isolation in the repository layer

This is the actual security boundary — per the plan, it must not depend on
routers remembering to filter.

- `huerise/infrastructure/database/repository.py`: add
  `TenantScopedRepository[ORM: TenantEntity, Domain](Repository[ORM, Domain])`
  overriding `find_by_id`, `find_by`, `find_all`, `delete_by_id`, `exists`
  to always require and filter by `tenant_id`, and `save` to stamp
  `tenant_id` from the domain object onto the ORM row.
- Concrete repos for Alarm/Profile/Occurrence/Sonos-selection/Hue-selection
  switch their base from `Repository` to `TenantScopedRepository`.
- Application services (`AlarmService`, `AlarmProfileService`,
  `HueBridgeService`, `SonosSpeakerService`, etc.) gain an explicit
  `tenant_id: UUID` parameter on every public method — deliberately
  explicit and greppable rather than smuggled through DI-scoped implicit
  context, since this is the exact boundary a mistake here would breach.
- Routers pass `current_user.tenant_id` (from `Depends(get_current_user)`)
  into every service call.
- `AlarmService`'s existing hardware-assignment validation (room exists on
  bridge → room belongs to tenant → scene belongs to room → profile belongs
  to tenant → audio output belongs to tenant, per the plan's "Hardware-
  Zuordnung und Validierung" section) extends to check `HueRoomAssignmentModel`;
  first alarm referencing an unclaimed room claims it for that tenant,
  matching the plan's deliberately-open room/scene ownership split.
- Update all touched tests (repository tests now pass `tenant_id`; add
  cross-tenant rejection tests — reading/writing another tenant's alarm by
  ID must 404, per the plan's own test checklist).

**Checkpoint**: full test suite green including new cross-tenant isolation
tests — this is the main isolation-boundary review point.

## Stage 6 — Scheduler & Runner: explicit privileged access

- `huerise/features/scheduler/application/scheduler.py`: `_materialise`
  (`uow.alarms.find_enabled()`) and `_claim_due` (`uow.occurrences.find_due(now)`)
  are legitimately cross-tenant (a background loop has no request/JWT).
  Rename/document them as explicitly privileged (e.g.
  `find_enabled_across_tenants`) so they read as intentional, not an
  accidental bypass of `TenantScopedRepository` — per the plan's "systemweite
  Hintergrundprozesse benötigen einen ausdrücklich erkennbaren privilegierten
  Zugriff."
- Returned `Alarm`/`AlarmOccurrence` domain objects already carry their own
  `tenant_id` (Stage 4) — `huerise/features/runner/application/runner.py`
  threads `occurrence.tenant_id` through its calls to load that tenant's
  profile, room, and audio output, so one tenant's alarm never touches
  another's resources.

## Stage 7 — Event stream & next-alarm isolation

- Event envelope gains `tenant_id` wherever `EventPublisher.publish(...)`
  is called.
- `huerise/features/events/application/hub.py`: `EventStreamHub.subscribe`
  takes `tenant_id`; `_fan_out` and `_replay_after` filter by it.
- `event_stream_router.py`: passes `current_user.tenant_id` into
  `hub.subscribe(...)`.
- `huerise/features/events/application/next_alarm.py`: `NextAlarmTracker`'s
  single `self._current` becomes a `dict[tenant_id, ...]`, computed from
  the scheduler's cross-tenant alarm list but keyed and emitted per tenant.

## Stage 8 — Resolve remaining process-wide singletons

- `SwitchableAudioPlayer` (`huerise/features/devices/application/audio_output.py`):
  single `_active: AudioOutput` becomes tenant-scoped — since a physical
  output belongs to exactly one tenant (plan's exclusivity rule), build a
  `tenant_id -> AudioPlayer` mapping at startup (mirrors today's Sonos
  restore-on-boot logic in `huerise/features/devices/infrastructure/di.py:150`),
  so stopping/snoozing one tenant's alarm can't touch another's playback.

## Stage 9 — Security/behavior test pass

Work through `plans/MULTI_TENANT_SUPPORT.md`'s own "Sicherheits- und
Verhaltenstests" section as an explicit checklist and add any test still
missing after Stages 1–8: foreign-resource-assignment rejection, parallel
alarms on independent hardware, scheduler/runner correct tenant context,
event replay isolation, migrated single-user data working post-upgrade.

## Verification (throughout)

- `uv run pytest` after each stage.
- `uv run ruff check .` (project lint config in `pyproject.toml`).
- `make check-generated` after any OpenAPI-surface change (Stage 2, Stage
  3) to confirm the Go client is in sync.
- Manual smoke test via `curl`/the CLI for the auth flow (Stage 2/3) since
  it's the part a type checker can't validate.
- For the tenant migration (Stage 4), run the Alembic upgrade against a
  copy of the real `data/daylight.db` (see `docs/adminer.md`) and inspect
  via Adminer that rows landed under the expected initial tenant.
