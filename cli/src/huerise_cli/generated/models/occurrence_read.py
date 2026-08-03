from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, Self, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.occurrence_state import OccurrenceState

T = TypeVar("T", bound="OccurrenceRead")


@_attrs_define
class OccurrenceRead:
    """
    Attributes:
        id (UUID):
        alarm_id (UUID):
        scheduled_for (datetime.datetime):
        state (OccurrenceState):
        triggered_at (datetime.datetime | None):
        finished_at (datetime.datetime | None):
        snooze_count (int):
        failure_reason (None | str):
    """

    id: UUID
    alarm_id: UUID
    scheduled_for: datetime.datetime
    state: OccurrenceState
    triggered_at: datetime.datetime | None
    finished_at: datetime.datetime | None
    snooze_count: int
    failure_reason: None | str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        alarm_id = str(self.alarm_id)

        scheduled_for = self.scheduled_for.isoformat()

        state = self.state.value

        triggered_at: None | str
        if isinstance(self.triggered_at, datetime.datetime):
            triggered_at = self.triggered_at.isoformat()
        else:
            triggered_at = self.triggered_at

        finished_at: None | str
        if isinstance(self.finished_at, datetime.datetime):
            finished_at = self.finished_at.isoformat()
        else:
            finished_at = self.finished_at

        snooze_count = self.snooze_count

        failure_reason: None | str
        failure_reason = self.failure_reason

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "alarm_id": alarm_id,
                "scheduled_for": scheduled_for,
                "state": state,
                "triggered_at": triggered_at,
                "finished_at": finished_at,
                "snooze_count": snooze_count,
                "failure_reason": failure_reason,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls, src_dict: Mapping[str, Any]) -> Self:
        d = dict(src_dict)
        id = UUID(d.pop("id"))

        alarm_id = UUID(d.pop("alarm_id"))

        scheduled_for = datetime.datetime.fromisoformat(d.pop("scheduled_for"))

        state = OccurrenceState(d.pop("state"))

        def _parse_triggered_at(data: object) -> datetime.datetime | None:
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                triggered_at_type_0 = datetime.datetime.fromisoformat(data)

                return triggered_at_type_0
            except TypeError, ValueError, AttributeError, KeyError:
                pass
            return cast(datetime.datetime | None, data)

        triggered_at = _parse_triggered_at(d.pop("triggered_at"))

        def _parse_finished_at(data: object) -> datetime.datetime | None:
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                finished_at_type_0 = datetime.datetime.fromisoformat(data)

                return finished_at_type_0
            except TypeError, ValueError, AttributeError, KeyError:
                pass
            return cast(datetime.datetime | None, data)

        finished_at = _parse_finished_at(d.pop("finished_at"))

        snooze_count = d.pop("snooze_count")

        def _parse_failure_reason(data: object) -> None | str:
            if data is None:
                return data
            return cast(None | str, data)

        failure_reason = _parse_failure_reason(d.pop("failure_reason"))

        occurrence_read = cls(
            id=id,
            alarm_id=alarm_id,
            scheduled_for=scheduled_for,
            state=state,
            triggered_at=triggered_at,
            finished_at=finished_at,
            snooze_count=snooze_count,
            failure_reason=failure_reason,
        )

        occurrence_read.additional_properties = d
        return occurrence_read

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
