import os
import tempfile
from pathlib import Path
from typing import Any, Self
from uuid import UUID

import yaml
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    IPvAnyAddress,
    StrictInt,
    StrictStr,
    ValidationError,
    model_validator,
)


class ConfigurationIssue(BaseModel):
    location: str
    message: str
    type: str


class ConfigurationError(Exception):
    def __init__(self, message: str, issues: list[ConfigurationIssue] | None = None):
        super().__init__(message)
        self.issues = issues or []


class NamedResourceConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    name: StrictStr = Field(min_length=1)


class AfterAlarmConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    room: NamedResourceConfig
    scene: NamedResourceConfig
    brightness: StrictInt = Field(ge=1, le=100)
    delay_seconds: StrictInt = Field(ge=0)


class DaylightAlarmConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    room: NamedResourceConfig
    scene: NamedResourceConfig
    start_brightness: StrictInt = Field(ge=1, le=100)
    end_brightness: StrictInt = Field(ge=1, le=100)
    duration_seconds: StrictInt = Field(gt=0)
    after_alarm: AfterAlarmConfig | None = None

    @model_validator(mode="after")
    def require_increasing_brightness(self) -> Self:
        if self.end_brightness <= self.start_brightness:
            raise ValueError("end_brightness must be greater than start_brightness")
        return self


class HueConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    bridge_id: StrictStr | None = Field(default=None, min_length=1)
    bridge_ip: IPvAnyAddress
    app_key: StrictStr | None = Field(default=None, min_length=20)


class HueriseConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    daylight_alarm: DaylightAlarmConfig
    hue: HueConfig | None = None


class YamlConfiguration:
    def __init__(self, path: Path) -> None:
        self.path = path

    def load(self) -> HueriseConfig:
        return self._validate(HueriseConfig, self._read())

    def load_hue(self) -> HueConfig | None:
        raw = self._read(required=False)
        if "hue" not in raw:
            return None
        return self._validate(HueConfig, raw["hue"], prefix="hue")

    def save_hue(self, hue: HueConfig) -> None:
        raw = self._read(required=False)
        raw["hue"] = hue.model_dump(mode="json", exclude_none=True)
        self._write(raw)

    def save_daylight_alarm(self, alarm: DaylightAlarmConfig) -> None:
        raw = self._read(required=False)
        raw["daylight_alarm"] = alarm.model_dump(mode="json")
        self._write(raw)

    def _read(self, *, required: bool = True) -> dict[str, Any]:
        try:
            contents = self.path.read_text(encoding="utf-8")
        except FileNotFoundError as error:
            if not required:
                return {}
            raise ConfigurationError(
                f"Configuration file not found: {self.path}"
            ) from error

        try:
            raw = yaml.safe_load(contents)
        except yaml.YAMLError as error:
            raise ConfigurationError(f"Invalid YAML: {error}") from error

        if raw is None and not required:
            return {}
        if not isinstance(raw, dict):
            raise ConfigurationError("Configuration root must be a mapping")
        return raw

    @staticmethod
    def _validate(
        model: type[BaseModel], raw: Any, *, prefix: str | None = None
    ) -> Any:
        try:
            return model.model_validate(raw)
        except ValidationError as error:
            issues = [
                ConfigurationIssue(
                    location=".".join(
                        str(part)
                        for part in ((prefix,) if prefix else ()) + item["loc"]
                    ),
                    message=item["msg"],
                    type=item["type"],
                )
                for item in error.errors()
            ]
            raise ConfigurationError("Configuration is invalid", issues) from error

    def _write(self, raw: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                newline="\n",
                dir=self.path.parent,
                prefix=f".{self.path.name}.",
                suffix=".tmp",
                delete=False,
            ) as temporary:
                yaml.safe_dump(raw, temporary, sort_keys=False)
                temporary_path = Path(temporary.name)
            os.replace(temporary_path, self.path)
        finally:
            if temporary_path is not None and temporary_path.exists():
                temporary_path.unlink()
