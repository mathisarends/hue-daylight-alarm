from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Self, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.audio_output import AudioOutput

T = TypeVar("T", bound="AudioOutputRead")


@_attrs_define
class AudioOutputRead:
    """The device sounds are currently played on.

    Attributes:
        active (AudioOutput): Where alarm and preview audio is played.
        available (list[AudioOutput]):
    """

    active: AudioOutput
    available: list[AudioOutput]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        active = self.active.value

        available = []
        for available_item_data in self.available:
            available_item = available_item_data.value
            available.append(available_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "active": active,
                "available": available,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls, src_dict: Mapping[str, Any]) -> Self:
        d = dict(src_dict)
        active = AudioOutput(d.pop("active"))

        available = []
        _available = d.pop("available")
        for available_item_data in _available:
            available_item = AudioOutput(available_item_data)

            available.append(available_item)

        audio_output_read = cls(
            active=active,
            available=available,
        )

        audio_output_read.additional_properties = d
        return audio_output_read

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
