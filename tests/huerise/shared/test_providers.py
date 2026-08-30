from pathlib import Path

import pytest

from huerise.configuration import YamlConfiguration
from huerise.env import AppSettings, HueEnvironment
from huerise.shared import CoreProvider


def test_core_provider_builds_environment_backed_dependencies(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HUERISE_API_KEY", "test-key")
    monkeypatch.setenv("HUERISE_CONFIG_PATH", "custom.yml")
    monkeypatch.delenv("HUE_BRIDGE_IP", raising=False)
    monkeypatch.delenv("HUE_APP_KEY", raising=False)
    provider = CoreProvider()

    settings = provider.app_settings()
    environment = provider.hue_environment()
    configuration = provider.configuration(settings)

    assert isinstance(settings, AppSettings)
    assert environment == HueEnvironment(_env_file=None)
    assert isinstance(configuration, YamlConfiguration)
    assert configuration.path == Path("custom.yml")
