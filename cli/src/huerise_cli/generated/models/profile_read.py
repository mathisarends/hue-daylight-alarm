from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, Self, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.intro_schema import IntroSchema
    from ..models.ringtone_schema import RingtoneSchema
    from ..models.sunrise_schema import SunriseSchema


T = TypeVar("T", bound="ProfileRead")


@_attrs_define
class ProfileRead:
    """Everything a profile is created with, plus what the server owns.

    Attributes:
        name (str):
        intro (IntroSchema):
        ringtone (RingtoneSchema):
        id (UUID):
        is_default (bool):
        sunrise (SunriseSchema | Unset):
    """

    name: str
    intro: IntroSchema
    ringtone: RingtoneSchema
    id: UUID
    is_default: bool
    sunrise: SunriseSchema | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        intro = self.intro.to_dict()

        ringtone = self.ringtone.to_dict()

        id = str(self.id)

        is_default = self.is_default

        sunrise: dict[str, Any] | Unset = UNSET
        if not isinstance(self.sunrise, Unset):
            sunrise = self.sunrise.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "intro": intro,
                "ringtone": ringtone,
                "id": id,
                "is_default": is_default,
            }
        )
        if sunrise is not UNSET:
            field_dict["sunrise"] = sunrise

        return field_dict

    @classmethod
    def from_dict(cls, src_dict: Mapping[str, Any]) -> Self:
        from ..models.intro_schema import IntroSchema
        from ..models.ringtone_schema import RingtoneSchema
        from ..models.sunrise_schema import SunriseSchema

        d = dict(src_dict)
        name = d.pop("name")

        intro = IntroSchema.from_dict(d.pop("intro"))

        ringtone = RingtoneSchema.from_dict(d.pop("ringtone"))

        id = UUID(d.pop("id"))

        is_default = d.pop("is_default")

        _sunrise = d.pop("sunrise", UNSET)
        sunrise: SunriseSchema | Unset
        if isinstance(_sunrise, Unset):
            sunrise = UNSET
        else:
            sunrise = SunriseSchema.from_dict(_sunrise)

        profile_read = cls(
            name=name,
            intro=intro,
            ringtone=ringtone,
            id=id,
            is_default=is_default,
            sunrise=sunrise,
        )

        profile_read.additional_properties = d
        return profile_read

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
