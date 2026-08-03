from collections.abc import Generator
from contextlib import contextmanager

from huerise_cli.config import Config
from huerise_cli.generated.client import AuthenticatedClient


@contextmanager
def api_client(config: Config) -> Generator[AuthenticatedClient]:
    with AuthenticatedClient(base_url=config.base_url, token=config.token) as client:
        yield client
