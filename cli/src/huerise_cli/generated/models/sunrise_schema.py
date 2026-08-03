from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Self, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="SunriseSchema")


@_attrs_define
class SunriseSchema:
    """
    Attributes:
        scene_name (str | Unset): Name of a Hue scene from GET /rooms/{room_name}. Default: 'Tageslichtwecker'.
        duration_minutes (int | Unset):  Default: 7.
        brightness_start (int | Unset):  Default: 1.
        brightness_end (int | Unset):  Default: 100.
    """

    scene_name: str | Unset = "Tageslichtwecker"
    duration_minutes: int | Unset = 7
    brightness_start: int | Unset = 1
    brightness_end: int | Unset = 100
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        scene_name = self.scene_name

        duration_minutes = self.duration_minutes

        brightness_start = self.brightness_start

        brightness_end = self.brightness_end

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if scene_name is not UNSET:
            field_dict["scene_name"] = scene_name
        if duration_minutes is not UNSET:
            field_dict["duration_minutes"] = duration_minutes
        if brightness_start is not UNSET:
            field_dict["brightness_start"] = brightness_start
        if brightness_end is not UNSET:
            field_dict["brightness_end"] = brightness_end

        return field_dict

    @classmethod
    def from_dict(cls, src_dict: Mapping[str, Any]) -> Self:
        d = dict(src_dict)
        scene_name = d.pop("scene_name", UNSET)

        duration_minutes = d.pop("duration_minutes", UNSET)

        brightness_start = d.pop("brightness_start", UNSET)

        brightness_end = d.pop("brightness_end", UNSET)

        sunrise_schema = cls(
            scene_name=scene_name,
            duration_minutes=duration_minutes,
            brightness_start=brightness_start,
            brightness_end=brightness_end,
        )

        sunrise_schema.additional_properties = d
        return sunrise_schema

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
