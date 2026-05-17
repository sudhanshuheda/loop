#!/usr/bin/env python3
"""Negative tests: confirm the Loop schemas reject obviously wrong inputs.

This complements tools/validate.py (which proves valid examples validate).
Together they prove the schemas are neither too strict nor too permissive.
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012

REPO_ROOT  = Path(__file__).resolve().parent.parent
SCHEMA_DIR = REPO_ROOT / "schemas" / "v0.1"
EXAMPLES   = REPO_ROOT / "examples"


def load_registry() -> Registry:
    resources: list[tuple[str, Resource]] = []
    for path in SCHEMA_DIR.glob("*.schema.json"):
        schema = json.loads(path.read_text())
        resource = Resource(contents=schema, specification=DRAFT202012)
        if "$id" in schema:
            resources.append((schema["$id"], resource))
        resources.append((path.name, resource))
    return Registry().with_resources(resources)


def load(p: Path) -> dict:
    return json.loads(p.read_text())


def expect_fail(label: str, schema_name: str, instance: dict, registry: Registry) -> bool:
    schema  = json.loads((SCHEMA_DIR / schema_name).read_text())
    errors  = list(Draft202012Validator(schema, registry=registry).iter_errors(instance))
    if errors:
        print(f"ok    {label}  ({len(errors)} error(s) as expected)")
        return True
    print(f"FAIL  {label}  -- expected validation to fail but it passed")
    return False


def main() -> int:
    registry = load_registry()
    rfq      = load(EXAMPLES / "freight-rfq.json")
    quote    = load(EXAMPLES / "freight-quote.json")
    decline  = load(EXAMPLES / "freight-decline.json")
    info_req = load(EXAMPLES / "clarification-info-request.json")
    passed   = True

    # RFQ line_items MUST NOT carry unit_price or rate_basis
    bad = copy.deepcopy(rfq)
    bad["body"]["line_items"][0]["unit_price"] = {"amount": "1.85", "currency": "USD"}
    passed &= expect_fail("RFQ rejects unit_price on line item", "rfq.schema.json", bad, registry)

    bad = copy.deepcopy(rfq)
    bad["body"]["line_items"][0]["rate_basis"] = "per_kg"
    passed &= expect_fail("RFQ rejects rate_basis on line item", "rfq.schema.json", bad, registry)

    # Quote line_items MUST carry both unit_price AND rate_basis
    bad = copy.deepcopy(quote)
    del bad["body"]["line_items"][0]["unit_price"]
    passed &= expect_fail("Quote requires unit_price on line item", "quote.schema.json", bad, registry)

    bad = copy.deepcopy(quote)
    del bad["body"]["line_items"][0]["rate_basis"]
    passed &= expect_fail("Quote requires rate_basis on line item", "quote.schema.json", bad, registry)

    # Money.amount must be a decimal string, not a number
    bad = copy.deepcopy(quote)
    bad["body"]["total"]["amount"] = 2848.16
    passed &= expect_fail("Money rejects float amount", "quote.schema.json", bad, registry)

    # Decline requires a reason_code from the enum
    bad = copy.deepcopy(decline)
    bad["body"]["reason_code"] = "we_dont_feel_like_it"
    passed &= expect_fail("Decline rejects unknown reason_code", "decline.schema.json", bad, registry)

    # Envelope requires recipients
    bad = copy.deepcopy(rfq)
    del bad["recipients"]
    passed &= expect_fail("Envelope requires recipients", "rfq.schema.json", bad, registry)

    # Currency must be 3 uppercase letters
    bad = copy.deepcopy(quote)
    bad["body"]["total"]["currency"] = "usd"
    passed &= expect_fail("Money rejects lowercase currency", "quote.schema.json", bad, registry)

    # New envelope fields are required: message_action
    bad = copy.deepcopy(rfq)
    del bad["message_action"]
    passed &= expect_fail("Envelope requires message_action", "rfq.schema.json", bad, registry)

    # New envelope fields are required: issuer_role
    bad = copy.deepcopy(rfq)
    del bad["issuer_role"]
    passed &= expect_fail("Envelope requires issuer_role", "rfq.schema.json", bad, registry)

    # issuer_role must be from the enum
    bad = copy.deepcopy(rfq)
    bad["issuer_role"] = "ceo"
    passed &= expect_fail("Envelope rejects unknown issuer_role", "rfq.schema.json", bad, registry)

    # RFQ message_action must be one of rfq_initial/modification/addition
    bad = copy.deepcopy(rfq)
    bad["message_action"] = "quote_provided"
    passed &= expect_fail("RFQ rejects non-RFQ message_action", "rfq.schema.json", bad, registry)

    # info_request requires at least one question
    bad = copy.deepcopy(info_req)
    bad["body"]["questions"] = []
    passed &= expect_fail("info_request requires >=1 question", "info_request.schema.json", bad, registry)

    # extraction_meta confidence must be in [0,1]
    bad = copy.deepcopy(rfq)
    bad["extraction_meta"]["extraction_confidence"] = 1.5
    passed &= expect_fail("extraction_meta confidence capped at 1.0", "rfq.schema.json", bad, registry)

    print()
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
