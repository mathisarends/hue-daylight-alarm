# Scheduler: port `cara/libs/scheduler`, adopt APScheduler, or keep ours?

Recommendation up front: **keep `AlarmScheduler`.** Neither the cara library
nor APScheduler replaces it, because they solve a different problem than the
one huerise actually has. But there is one concrete idea worth stealing from
cara (sleep-until-due instead of a fixed 30 s tick), and that is the change I
would make.

## The two problems are not the same

`cara/libs/scheduler` and APScheduler both answer:

> "Call this callable at time T, and remember the job across restarts."

Jobs are opaque payloads. The store is bookkeeping for the timer loop. Whoever
registered the job owns its meaning.

`huerise/features/scheduler` answers something else:

> "Project alarm *rules* into persisted `AlarmOccurrence` aggregates, claim
> due ones atomically, emit domain events, and retire one-time alarms."

The occurrence is not bookkeeping — it is domain state the rest of the system
reads and writes. `GET /alarms/{id}` shows the next occurrence, the runner
transitions it `PENDING → SUNRISE → DISMISSED`, the event stream carries
`OccurrenceScheduled` / `OccurrenceSkipped`, and `find_due` + the unique
`(alarm_id, scheduled_for)` constraint are what make the whole thing safe.

This is a **materialiser / outbox poller**, not a timer. Swapping in a timer
library does not remove that code; it adds a second scheduling mechanism
alongside it.

## What we would actually lose

| Concern | What we have | What a job library gives |
| --- | --- | --- |
| Wall-clock + DST | `Schedule` with `fold=0`, deliberate spring-forward / fall-back semantics, typed `frozenset[Weekday]` | cron string `30 6 * * 1,2,3`, croniter's own DST behaviour |
| Claiming a run | `start_sunrise()` inside a UoW transaction — an atomic state transition in Postgres | cara: none (README says two processes can double-run). APScheduler 3: none. APScheduler 4: leases, but see below |
| Missed while offline | `_GRACE_PERIOD` → `skip()` + `OccurrenceSkipped` event | cara `Interval`: silently jumps forward. Cron: silently computes next. Neither can express "mark it skipped and tell the client" |
| Idempotence | Unique constraint on `(alarm_id, scheduled_for)`; a restart mid-day cannot duplicate | cara reloads jobs and re-sleeps; at-least-once by design |
| Visible history | `alarm_occurrences` rows with state, `triggered_at`, `failure_reason` | job row disappears when the job is done |

The DST point is the one I would not give up. `Schedule.next_occurrence` is a
small, tested, explicitly-documented piece of domain logic. Encoding weekday
sets as cron expressions makes it implicit and moves the DST decision into
croniter, where it is neither documented nor ours.

## On the cara library specifically

It is a good library *for cara*. Two things make it a poor fit here:

1. **Persistence mismatch.** `SqliteJobStore` + a `Codec`. huerise is Postgres
   via SQLModel/Alembic with a `UnitOfWork`. We would have to write a
   `PostgresJobStore` adapter — and still keep `alarm_occurrences`, because
   that table is domain state, not job state. Two tables, two lifecycles.
2. **One asyncio task per job, sleeping until due.** Fine for a handful of
   heartbeats. With multi-tenant alarms it is a task per alarm per process,
   and with more than one API replica every job fires N times — the README is
   honest about this ("V1 does not lease jobs across processes"). Our tick +
   DB claim scales to replicas today.

Integrating it as a workspace package is also more friction than it looks:
huerise is a single-package project, not a uv workspace. Adding
`[tool.uv.workspace]` and a `libs/` tree to consume ~300 lines is a structural
change to the repo for a dependency we would use once.

## On APScheduler

APScheduler 3 stores jobs by **pickling a reference to the callable**
(`module:function`). Renaming or moving a function silently breaks jobs that
are already in the database. It also brings its own executor and threading
model, its own `misfire_grace_time` / `coalesce` knobs that partly duplicate
`_GRACE_PERIOD`, and no distributed locking. APScheduler 4 fixes the locking
(a data store with leases) and is the better design, but it is a much heavier
runtime to sit under a feature that currently needs one `while True` loop —
and we would still write the occurrence materialisation on top of it.

Worth reconsidering only if huerise grows a real background-job surface:
user-submitted schedules of arbitrary kinds, retries with backoff, a job
dashboard. Today there is exactly **one** periodic loop in the codebase
(`grep asyncio.sleep` finds the scheduler, the runner's sunrise steps, and the
demo replay — the latter two are step timers, not schedules). One loop does
not justify a scheduling framework.

## The one thing worth porting: sleep until due

This is where cara is genuinely better. `_run_job` sleeps exactly until
`next_run_at`; we poll every 30 s, so an alarm set for 07:00:00 can fire at
07:00:29. For a sunrise that jitter is visible.

The fix does not need a library — keep the tick as the safety net, but let the
next materialised occurrence shorten the sleep:

```python
async def run(self) -> None:
    while True:
        try:
            await self.tick()
        except Exception:
            logger.exception("Scheduler tick failed")
        await asyncio.sleep(await self._sleep_seconds())

async def _sleep_seconds(self) -> float:
    """Wake on the next due occurrence, but never sleep past a tick.

    The tick bound keeps us picking up alarms created by other replicas.
    """
    async with self._unit_of_work_factory.create() as uow:
        earliest = await uow.occurrences.earliest_pending()
    ceiling = self._tick_interval.total_seconds()
    if earliest is None:
        return ceiling
    remaining = (earliest - datetime.now(UTC)).total_seconds()
    return min(max(remaining, 0.0), ceiling)
```

Cost: one repository method (`earliest_pending`) and a few lines. Benefit:
sub-second firing accuracy, and the tick still bounds how stale our view of
the table can get, so a second replica adding an alarm is still noticed.

An `asyncio.Event` set by `AlarmService` on create/update would cut the last
30 s of staleness in a single-process deployment, but it does not survive
multiple replicas, so it is a nice-to-have rather than the fix.

## Summary

- Don't port cara's library. It is a timer with a job store; we need a
  materialiser over a domain aggregate, and we would end up keeping both.
- Don't adopt APScheduler. v3's pickled callables are a maintenance hazard and
  v4 is a heavy runtime for one loop. Revisit if a generic job surface appears.
- Do steal the sleep-until-due idea. Bounded by the existing tick, it removes
  the up-to-30 s firing jitter without adding a dependency.
