from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Self, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="RingtoneSchema")


@_attrs_define
class RingtoneSchema:
    """
    Attributes:
        sound_id (UUID): Id of a sound from GET /sounds, e.g. 'wake_up/bowls'.
        volume (int | Unset):  Default: 80.
    """

    sound_id: UUID
    volume: int | Unset = 80
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        sound_id = str(self.sound_id)

        volume = self.volume

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "sound_id": sound_id,
            }
        )
        if volume is not UNSET:
            field_dict["volume"] = volume

        return field_dict

    @classmethod
    def from_dict(cls, src_dict: Mapping[str, Any]) -> Self:
        d = dict(src_dict)
        sound_id = UUID(d.pop("sound_id"))

        volume = d.pop("volume", UNSET)

        ringtone_schema = cls(
            sound_id=sound_id,
            volume=volume,
        )

        ringtone_schema.additional_properties = d
        return ringtone_schema

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
