import json
from pathlib import Path
from typing import Any

from huerise.main import app


def _normalize_optional_parameters(spec: dict[str, Any]) -> None:
    """Represent optional HTTP parameters through `required`, not JSON null."""
    for path_item in spec.get("paths", {}).values():
        for operation in path_item.values():
            if not isinstance(operation, dict):
                continue
            for parameter in operation.get("parameters", []):
                if parameter.get("required", False):
                    continue
                schema = parameter.get("schema", {})
                variants = schema.get("anyOf")
                if not isinstance(variants, list):
                    continue
                non_null = [item for item in variants if item.get("type") != "null"]
                if len(non_null) == 1 and len(non_null) != len(variants):
                    title = schema.get("title")
                    schema.clear()
                    schema.update(non_null[0])
                    if title is not None:
                        schema["title"] = title


if __name__ == "__main__":
    output = Path(__file__).resolve().parent.parent / "openapi.json"
    spec = app.openapi()
    _normalize_optional_parameters(spec)
    output.write_text(json.dumps(spec, indent=2) + "\n")
    print(f"Wrote {output}")
