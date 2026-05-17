#!/usr/bin/env python3
"""Validate every Loop example against its schema.

Resolves paths relative to the repo root (this script's grandparent),
so it works regardless of the CWD. Exits non-zero on any failure so it
can be wired into CI.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012

REPO_ROOT   = Path(__file__).resolve().parent.parent
SCHEMA_DIR  = REPO_ROOT / "schemas" / "v0.1"
EXAMPLES    = REPO_ROOT / "examples"

CASES: list[tuple[str, str]] = [
    ("freight-rfq.json",                  "rfq.schema.json"),
    ("freight-quote.json",                "quote.schema.json"),
    ("freight-po.json",                   "po.schema.json"),
    ("freight-decline.json",              "decline.schema.json"),
    ("services-rfp.json",                 "rfq.schema.json"),
    ("fcl-sea-rfq.json",                  "rfq.schema.json"),
    ("hazmat-air-rfq.json",               "rfq.schema.json"),
    ("clarification-info-request.json",   "info_request.schema.json"),
    ("clarification-info-provided.json",  "info_provided.schema.json"),
]


def load_registry() -> Registry:
    """Build a referencing Registry covering every schema by both its
    canonical $id and its bare filename (matches how the message schemas
    reference common.schema.json by relative filename)."""
    resources: list[tuple[str, Resource]] = []
    for path in SCHEMA_DIR.glob("*.schema.json"):
        schema = json.loads(path.read_text())
        resource = Resource(contents=schema, specification=DRAFT202012)
        if "$id" in schema:
            resources.append((schema["$id"], resource))
        resources.append((path.name, resource))
    return Registry().with_resources(resources)


def errors_for(example_path: Path, schema_name: str, registry: Registry) -> list[str]:
    schema   = json.loads((SCHEMA_DIR / schema_name).read_text())
    instance = json.loads(example_path.read_text())
    validator = Draft202012Validator(schema, registry=registry)
    return [
        f"  {' / '.join(str(p) for p in err.absolute_path) or '<root>'}: {err.message}"
        for err in validator.iter_errors(instance)
    ]


def main() -> int:
    registry = load_registry()
    total = 0
    for example_name, schema_name in CASES:
        errs = errors_for(EXAMPLES / example_name, schema_name, registry)
        if errs:
            total += len(errs)
            print(f"FAIL  {example_name}  (against {schema_name})")
            for e in errs:
                print(e)
        else:
            print(f"ok    {example_name}  (against {schema_name})")
    print()
    if total:
        print(f"{total} validation error(s)")
        return 1
    print(f"All {len(CASES)} examples validate.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
