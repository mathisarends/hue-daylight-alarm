import pytest
from pydantic import ValidationError

from huerise.features.devices.infrastructure.settings import HueEnvironment


def test_hue_environment_can_be_unconfigured() -> None:
    settings = HueEnvironment(_env_file=None)

    assert settings.configured is False


def test_hue_environment_requires_the_complete_override_pair() -> None:
    with pytest.raises(ValidationError, match="must either both be set"):
        HueEnvironment(bridge_ip="10.0.0.2", _env_file=None)


def test_hue_environment_accepts_a_complete_override() -> None:
    settings = HueEnvironment(
        bridge_ip="10.0.0.2", app_key="secret", _env_file=None
    )

    assert settings.configured is True
    assert settings.app_key is not None
    assert settings.app_key.get_secret_value() == "secret"
