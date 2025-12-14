from dataclasses import dataclass


@dataclass
class RegisteredSound:
    name: str
    relative_path: str
    category: str | None

    @property
    def display_name(self) -> str:
        return self.name.replace("-", " ").replace("_", " ").title()
