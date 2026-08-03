from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, Self, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.schedule_schema import ScheduleSchema


T = TypeVar("T", bound="AlarmCreate")


@_attrs_define
class AlarmCreate:
    """
    Attributes:
        label (str):
        schedule (ScheduleSchema): When an alarm fires, as wall-clock time in a named zone.
        room_name (str):
        profile_id (None | Unset | UUID): Defaults to the default profile.
    """

    label: str
    schedule: ScheduleSchema
    room_name: str
    profile_id: None | Unset | UUID = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        label = self.label

        schedule = self.schedule.to_dict()

        room_name = self.room_name

        profile_id: None | str | Unset
        if isinstance(self.profile_id, Unset):
            profile_id = UNSET
        elif isinstance(self.profile_id, UUID):
            profile_id = str(self.profile_id)
        else:
            profile_id = self.profile_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "label": label,
                "schedule": schedule,
                "room_name": room_name,
            }
        )
        if profile_id is not UNSET:
            field_dict["profile_id"] = profile_id

        return field_dict

    @classmethod
    def from_dict(cls, src_dict: Mapping[str, Any]) -> Self:
        from ..models.schedule_schema import ScheduleSchema

        d = dict(src_dict)
        label = d.pop("label")

        schedule = ScheduleSchema.from_dict(d.pop("schedule"))

        room_name = d.pop("room_name")

        def _parse_profile_id(data: object) -> None | Unset | UUID:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, str):
                    raise TypeError()
                profile_id_type_0 = UUID(data)

                return profile_id_type_0
            except TypeError, ValueError, AttributeError, KeyError:
                pass
            return cast(None | Unset | UUID, data)

        profile_id = _parse_profile_id(d.pop("profile_id", UNSET))

        alarm_create = cls(
            label=label,
            schedule=schedule,
            room_name=room_name,
            profile_id=profile_id,
        )

        alarm_create.additional_properties = d
        return alarm_create

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
