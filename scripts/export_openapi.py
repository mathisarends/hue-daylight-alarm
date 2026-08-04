import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from huerise.main import app

type Schema = dict[str, Any]

OUTPUT = Path(__file__).resolve().parent.parent / "openapi.json"


def _optional_parameter_schemas(spec: Schema) -> Iterator[Schema]:
    for path_item in spec.get("paths", {}).values():
        for operation in path_item.values():
            if not isinstance(operation, dict):
                continue
            for parameter in operation.get("parameters", []):
                schema = parameter.get("schema")
                if not parameter.get("required", False) and isinstance(schema, dict):
                    yield schema


def _unwrap_nullable(schema: Schema) -> None:
    """Represent optional HTTP parameters through `required`, not JSON null."""
    variants = schema.get("anyOf")
    if not isinstance(variants, list):
        return

    non_null = [variant for variant in variants if variant.get("type") != "null"]
    if len(non_null) != 1 or len(non_null) == len(variants):
        return

    title = schema.get("title")
    schema.clear()
    schema.update(non_null[0])
    if title is not None:
        schema["title"] = title


def _schemas_with_numeric_exclusive_bounds(spec: Schema) -> Iterator[Schema]:
    stack: list[Any] = [spec]
    while stack:
        node = stack.pop()
        if isinstance(node, dict):
            if any(
                key in node and not isinstance(node[key], bool)
                for key in ("exclusiveMinimum", "exclusiveMaximum")
            ):
                yield node
            stack.extend(node.values())
        elif isinstance(node, list):
            stack.extend(node)


def _use_draft4_exclusive_bounds(schema: Schema) -> None:
    """ogen only understands exclusiveMinimum/Maximum as booleans, not as the
    numeric bounds Pydantic emits for `gt`/`lt` under JSON Schema 2020-12."""
    for bound, exclusive_bound in (
        ("minimum", "exclusiveMinimum"),
        ("maximum", "exclusiveMaximum"),
    ):
        value = schema.get(exclusive_bound)
        if value is None or isinstance(value, bool):
            continue
        schema[bound] = value
        schema[exclusive_bound] = True


def main() -> None:
    spec = app.openapi()
    for schema in _optional_parameter_schemas(spec):
        _unwrap_nullable(schema)
    for schema in _schemas_with_numeric_exclusive_bounds(spec):
        _use_draft4_exclusive_bounds(schema)

    OUTPUT.write_text(json.dumps(spec, indent=2) + "\n")
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()
