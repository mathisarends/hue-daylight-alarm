import json
from pathlib import Path

from huerise.main import app

OUTPUT = Path(__file__).resolve().parent.parent / "specs" / "openapi.json"


def main() -> None:
    OUTPUT.write_text(json.dumps(app.openapi(), indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()
