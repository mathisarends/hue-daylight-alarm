from dataclasses import dataclass

from huerise.configuration import HueriseConfig


@dataclass
class FakeConfiguration:
    config: HueriseConfig

    def load(self) -> HueriseConfig:
        return self.config
