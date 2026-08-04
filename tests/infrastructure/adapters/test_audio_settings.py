import pytest
from pydantic import ValidationError

from huerise.features.devices.domain import AudioOutput
from huerise.features.devices.infrastructure.settings import AudioSettings


def test_single_backend_selects_itself(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AUDIO_BACKENDS", "sonos")

    settings = AudioSettings(_env_file=None)

    assert settings.backends == (AudioOutput.SONOS,)
    assert settings.initial_output is AudioOutput.SONOS


def test_all_backends_honour_the_configured_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AUDIO_BACKENDS", "all")
    monkeypatch.setenv("AUDIO_DEFAULT_OUTPUT", "sonos")

    settings = AudioSettings(_env_file=None)

    assert settings.backends == (AudioOutput.LOCAL, AudioOutput.SONOS)
    assert settings.initial_output is AudioOutput.SONOS


def test_empty_backend_configuration_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AUDIO_BACKENDS", "")

    with pytest.raises(ValidationError, match="configure at least one audio backend"):
        AudioSettings(_env_file=None)
