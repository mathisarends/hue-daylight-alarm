import json
from pathlib import Path

from huerise.main import app

if __name__ == "__main__":
    output = Path(__file__).resolve().parent.parent / "openapi.json"
    output.write_text(json.dumps(app.openapi(), indent=2) + "\n")
    print(f"Wrote {output}")
