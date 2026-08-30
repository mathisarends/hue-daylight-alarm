import json
from typing import get_args
from uuid import uuid4

import pytest
from pydantic import TypeAdapter

from huerise.features.alarm.domain import OccurrenceState
from huerise.features.events.domain import (
    AlarmCreated,
    AlarmSnapshot,
    AnyHueriseEvent,
    EventType,
    HueriseEvent,
    OccurrenceProgress,
    OccurrenceSnapshot,
    OccurrenceStarted,
)
from huerise.tests.application.conftest import make_alarm, make_occurrence

events = TypeAdapter[HueriseEvent](AnyHueriseEvent)


def union_members() -> tuple[type[HueriseEvent], ...]:
    annotated, _ = get_args(AnyHueriseEvent.__value__)
    return get_args(annotated)


def make_started() -> OccurrenceStarted:
    alarm = make_alarm()
    occurrence = make_occurrence(
        alarm.id, alarm.next_occurrence(), OccurrenceState.SUNRISE
    )
    return OccurrenceStarted(
        occurrence=OccurrenceSnapshot.from_domain(occurrence),
        label=alarm.label,
        room_name=alarm.room_name,
        sunrise_seconds=420,
    )


@pytest.mark.parametrize("event_type", list(EventType))
def test_every_event_type_has_exactly_one_class(event_type: EventType) -> None:
    """The catalogue and the union cannot drift apart unnoticed."""
    matches = [
        member
        for member in union_members()
        if member.model_fields["type"].default is event_type
    ]
    assert len(matches) == 1


def test_union_resolves_concrete_class_by_discriminator() -> None:
    original = AlarmCreated(alarm=AlarmSnapshot.from_domain(make_alarm()))

    restored = events.validate_json(original.model_dump_json())

    assert isinstance(restored, AlarmCreated)
    assert restored.alarm == original.alarm


@pytest.mark.parametrize("member", union_members())
def test_bus_routing_path_stays_off_the_wire(member: type[HueriseEvent]) -> None:
    schema = member.model_json_schema(mode="serialization")

    assert "path" not in schema["properties"]


def test_dispatch_path_is_not_serialised() -> None:
    event = make_started()
    event.path.append("bus-1")

    assert "path" not in json.loads(event.model_dump_json())


def test_causality_survives_serialisation() -> None:
    cause = AlarmCreated(alarm=AlarmSnapshot.from_domain(make_alarm()))
    effect = make_started()
    effect.parent_id = cause.id

    restored = events.validate_json(effect.model_dump_json())

    assert restored.parent_id == cause.id


@pytest.mark.parametrize(
    ("step", "total_steps", "expected"),
    [(0, 70, 1.4), (29, 70, 42.9), (69, 70, 100.0), (0, 1, 100.0)],
)
def test_progress_percent_is_derived_from_step(
    step: int, total_steps: int, expected: float
) -> None:
    progress = OccurrenceProgress(
        occurrence_id=uuid4(),
        alarm_id=uuid4(),
        brightness=42,
        step=step,
        total_steps=total_steps,
        elapsed_seconds=step * 6,
        total_seconds=total_steps * 6,
    )

    assert progress.percent == expected
    assert json.loads(progress.model_dump_json())["percent"] == expected
