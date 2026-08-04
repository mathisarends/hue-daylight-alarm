import os
from dataclasses import dataclass
from typing import Self

from dotenv import find_dotenv, load_dotenv

_DEFAULT_BASE_URL = "http://localhost:8000"

load_dotenv(find_dotenv(usecwd=True))


class ConfigError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class Config:
    base_url: str
    token: str

    @classmethod
    def from_env(cls) -> Self:
        # Falls back to the server's own token variable so a single .env
        # covers both without duplicating the value under two names.
        token = os.environ.get("HUERISE_API_TOKEN") or os.environ.get("API_ACCESS_TOKEN")
        if not token:
            raise ConfigError(
                "No API token found. Set HUERISE_API_TOKEN (or API_ACCESS_TOKEN) "
                "in your environment or in a .env file, e.g.\n"
                "  HUERISE_API_TOKEN=your-api-access-token"
            )
        return cls(
            base_url=os.environ.get("HUERISE_API_URL", _DEFAULT_BASE_URL),
            token=token,
        )
