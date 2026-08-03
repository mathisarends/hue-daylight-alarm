from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Self, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.weekday import Weekday
from ..types import UNSET, Unset

T = TypeVar("T", bound="ScheduleSchema")


@_attrs_define
class ScheduleSchema:
    """When an alarm fires, as wall-clock time in a named zone.

    Attributes:
        hour (int):
        minute (int):
        timezone (str | Unset): IANA zone. The alarm keeps its wall-clock time across DST. Default: 'Europe/Berlin'.
        days (list[Weekday] | Unset): Empty means the alarm fires once, then disables itself.
    """

    hour: int
    minute: int
    timezone: str | Unset = "Europe/Berlin"
    days: list[Weekday] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        hour = self.hour

        minute = self.minute

        timezone = self.timezone

        days: list[int] | Unset = UNSET
        if not isinstance(self.days, Unset):
            days = []
            for days_item_data in self.days:
                days_item = days_item_data.value
                days.append(days_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "hour": hour,
                "minute": minute,
            }
        )
        if timezone is not UNSET:
            field_dict["timezone"] = timezone
        if days is not UNSET:
            field_dict["days"] = days

        return field_dict

    @classmethod
    def from_dict(cls, src_dict: Mapping[str, Any]) -> Self:
        d = dict(src_dict)
        hour = d.pop("hour")

        minute = d.pop("minute")

        timezone = d.pop("timezone", UNSET)

        _days = d.pop("days", UNSET)
        days: list[Weekday] | Unset = UNSET
        if _days is not UNSET:
            days = []
            for days_item_data in _days:
                days_item = Weekday(days_item_data)

                days.append(days_item)

        schedule_schema = cls(
            hour=hour,
            minute=minute,
            timezone=timezone,
            days=days,
        )

        schedule_schema.additional_properties = d
        return schedule_schema

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
