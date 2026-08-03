import os
from dataclasses import dataclass
from typing import Self

_DEFAULT_BASE_URL = "http://localhost:8000"


class ConfigError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class Config:
    base_url: str
    token: str

    @classmethod
    def from_env(cls) -> Self:
        token = os.environ.get("HUERISE_API_TOKEN")
        if not token:
            raise ConfigError(
                "HUERISE_API_TOKEN is not set. Export the same value as the "
                "server's API_ACCESS_TOKEN, e.g.\n"
                "  export HUERISE_API_TOKEN=your-api-access-token"
            )
        return cls(
            base_url=os.environ.get("HUERISE_API_URL", _DEFAULT_BASE_URL),
            token=token,
        )
