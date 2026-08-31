from pathlib import Path
from uuid import UUID

import pytest
from pydantic import ValidationError

from huerise.configuration import ConfigurationError, HueConfig, YamlConfiguration
from huerise.env import AppSettings, HueEnvironment, LogLevel

VALID_CONFIG = """\
daylight_alarm:
  room:
    id: 00000000-0000-0000-0000-000000000002
    name: Bedroom
  scene:
    id: 00000000-0000-0000-0000-000000000001
    name: Sunrise
  start_brightness: 1
  end_brightness: 100
  duration_seconds: 1800
"""


def test_loads_daylight_alarm(tmp_path: Path) -> None:
    path = tmp_path / "huerise.yml"
    path.write_text(VALID_CONFIG, encoding="utf-8")

    config = YamlConfiguration(path).load()

    assert config.daylight_alarm.scene.id == UUID(int=1)
    assert config.daylight_alarm.room.name == "Bedroom"
    assert config.daylight_alarm.duration_seconds == 1800
    assert config.hue is None


@pytest.mark.parametrize(
    ("target", "replacement", "location"),
    [
        ("  end_brightness: 100\n", "", "daylight_alarm.end_brightness"),
        ("end_brightness: 100", "end_brightness: 1", "daylight_alarm"),
        (
            "duration_seconds: 1800",
            "duration_seconds: 0",
            "daylight_alarm.duration_seconds",
        ),
        (
            "duration_seconds: 1800",
            "duration_seconds: '1800'",
            "daylight_alarm.duration_seconds",
        ),
        (
            "duration_seconds: 1800",
            "duration_seconds: 1800\n  typo: true",
            "daylight_alarm.typo",
        ),
    ],
)
def test_rejects_invalid_alarm(
    tmp_path: Path, target: str, replacement: str, location: str
) -> None:
    path = tmp_path / "huerise.yml"
    path.write_text(VALID_CONFIG.replace(target, replacement), encoding="utf-8")

    with pytest.raises(ConfigurationError) as raised:
        YamlConfiguration(path).load()

    assert location in [issue.location for issue in raised.value.issues]


def test_reports_missing_and_malformed_files(tmp_path: Path) -> None:
    repository = YamlConfiguration(tmp_path / "huerise.yml")

    with pytest.raises(ConfigurationError, match="not found"):
        repository.load()

    repository.path.write_text("daylight_alarm: [", encoding="utf-8")
    with pytest.raises(ConfigurationError, match="Invalid YAML"):
        repository.load()


@pytest.mark.parametrize("contents", ["", "[]"])
def test_rejects_non_mapping_configuration_roots(tmp_path: Path, contents: str) -> None:
    path = tmp_path / "huerise.yml"
    path.write_text(contents, encoding="utf-8")

    with pytest.raises(ConfigurationError, match="root must be a mapping"):
        YamlConfiguration(path).load()


def test_empty_file_can_receive_initial_hue_configuration(tmp_path: Path) -> None:
    path = tmp_path / "huerise.yml"
    path.write_text("", encoding="utf-8")
    repository = YamlConfiguration(path)

    repository.save_hue(HueConfig(bridge_ip="192.0.2.10"))

    assert repository.load_hue() == HueConfig(bridge_ip="192.0.2.10")


def test_removes_temporary_file_when_atomic_replace_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository = YamlConfiguration(tmp_path / "huerise.yml")

    def fail_replace(_: Path, __: Path) -> None:
        raise OSError("disk unavailable")

    monkeypatch.setattr("huerise.configuration.os.replace", fail_replace)

    with pytest.raises(OSError, match="disk unavailable"):
        repository.save_hue(HueConfig(bridge_ip="192.0.2.10"))

    assert list(tmp_path.glob("*.tmp")) == []


def test_updates_only_hue_section_atomically(tmp_path: Path) -> None:
    path = tmp_path / "huerise.yml"
    path.write_text(VALID_CONFIG, encoding="utf-8")
    repository = YamlConfiguration(path)

    repository.save_hue(
        HueConfig(bridge_ip="192.0.2.10", app_key="a-valid-hue-app-key-123")
    )

    config = repository.load()
    assert str(config.hue.bridge_ip) == "192.0.2.10"
    assert config.hue.app_key == "a-valid-hue-app-key-123"
    assert config.daylight_alarm.scene.id == UUID(int=1)
    assert list(tmp_path.glob("*.tmp")) == []


def test_hue_can_be_onboarded_before_alarm_is_configured(tmp_path: Path) -> None:
    repository = YamlConfiguration(tmp_path / "huerise.yml")

    repository.save_hue(HueConfig(bridge_ip="192.0.2.10"))

    hue = repository.load_hue()
    assert hue is not None
    assert str(hue.bridge_ip) == "192.0.2.10"
    assert hue.app_key is None


def test_api_settings_use_huerise_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HUERISE_API_KEY", "test-key")
    monkeypatch.setenv("HUERISE_CONFIG_PATH", "custom.yml")
    monkeypatch.setenv("HUERISE_LOG_LEVEL", "DEBUG")

    settings = AppSettings(_env_file=None)

    assert settings.api_key.get_secret_value() == "test-key"
    assert settings.config_path == Path("custom.yml")
    assert settings.log_level is LogLevel.DEBUG


def test_hue_environment_requires_a_complete_pair(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("HUE_BRIDGE_IP", "192.0.2.10")
    monkeypatch.delenv("HUE_APP_KEY", raising=False)

    with pytest.raises(ValidationError, match="must either both be set"):
        HueEnvironment(_env_file=None)
