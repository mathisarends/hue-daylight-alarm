from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, Self, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.schedule_schema import ScheduleSchema


T = TypeVar("T", bound="AlarmRead")


@_attrs_define
class AlarmRead:
    """
    Attributes:
        id (UUID):
        label (str):
        schedule (ScheduleSchema): When an alarm fires, as wall-clock time in a named zone.
        room_name (str):
        profile_id (UUID):
        is_enabled (bool):
        created_at (datetime.datetime):
        next_occurrence (datetime.datetime | None):
    """

    id: UUID
    label: str
    schedule: ScheduleSchema
    room_name: str
    profile_id: UUID
    is_enabled: bool
    created_at: datetime.datetime
    next_occurrence: datetime.datetime | None
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        label = self.label

        schedule = self.schedule.to_dict()

        room_name = self.room_name

        profile_id = str(self.profile_id)

        is_enabled = self.is_enabled

        created_at = self.created_at.isoformat()

        next_occurrence: None | str
        if isinstance(self.next_occurrence, datetime.datetime):
            next_occurrence = self.next_occurrence.isoformat()
        else:
            next_occurrence = self.next_occurrence

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "label": label,
                "schedule": schedule,
                "room_name": room_name,
                "profile_id": profile_id,
                "is_enabled": is_enabled,
                "created_at": created_at,
                "next_occurrence": next_occurrence,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls, src_dict: Mapping[str, Any]) -> Self:
        from ..models.schedule_schema import ScheduleSchema

        d = dict(src_dict)
        id = UUID(d.pop("id"))

        label = d.pop("label")

        schedule = ScheduleSchema.from_dict(d.pop("schedule"))

        room_name = d.pop("room_name")

        profile_id = UUID(d.pop("profile_id"))

        is_enabled = d.pop("is_enabled")

        created_at = datetime.datetime.fromisoformat(d.pop("created_at"))

        def _parse_next_occurrence(data: object) -> datetime.datetime | None:
            if data is None:
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                next_occurrence_type_0 = datetime.datetime.fromisoformat(data)

                return next_occurrence_type_0
            except TypeError, ValueError, AttributeError, KeyError:
                pass
            return cast(datetime.datetime | None, data)

        next_occurrence = _parse_next_occurrence(d.pop("next_occurrence"))

        alarm_read = cls(
            id=id,
            label=label,
            schedule=schedule,
            room_name=room_name,
            profile_id=profile_id,
            is_enabled=is_enabled,
            created_at=created_at,
            next_occurrence=next_occurrence,
        )

        alarm_read.additional_properties = d
        return alarm_read

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
