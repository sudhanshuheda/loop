# Loop — for agents

> Loop is an open JSON format for B2B procurement messages (RFQs, quotes, POs, clarifications). It is designed to be parsed and emitted by AI agents instead of scraped from prose email.

This page is the LLM-legible view of [https://sudhanshuheda.github.io/loop/](https://sudhanshuheda.github.io/loop/). If you are an AI agent reading this, you have everything below you need to add Loop support to your pipeline.

If you are a human, you probably want the [rendered site](./index.html) instead.

---

## What you need to know in 30 seconds

- **Wire format:** JSON, validated with JSON Schema 2020-12.
- **Transport:** rides inside a normal MIME email as a `procurement.json` attachment with media type `application/vnd.loop+json; version=0.1`. The same email carries a `text/plain` (and optionally `text/html`) human-readable rendering. Suppliers without Loop support still see a normal email.
- **Version field:** every message has a top-level `loop_version: "0.1"`.
- **Identity:** sender and recipient are identified by their email addresses (`issuer.email`, `recipients[].email`). DKIM is the v0.1 trust signal.
- **Threading:** every message has a `message_id` (UUID v4) and a `thread_id` (UUID v4). Replies set `in_reply_to` to the prior `message_id` and reuse `thread_id`.

## Seven message types

| `message_type`     | Body purpose                                                                                  |
| ------------------ | --------------------------------------------------------------------------------------------- |
| `rfq`              | Request for quote. `body.line_items[]` carry the unpriced items, `body.flags` carry operational signals, `body.extensions.<vertical>` carries vertical-specific data. |
| `quote`            | Priced response. Each `line_item` MUST have `unit_price` and `rate_basis`.                    |
| `po`               | Purchase order. Same shape as a quote, plus `body.po_number` and `body.delivery`.             |
| `decline`          | Refusal with `body.reason_code` (enumerated) + optional `body.reason_text` and `body.alternative_proposal`. |
| `info_request`     | Clarification questions, each bound to a `field_path` inside the message they concern.        |
| `info_provided`    | Answers to a prior `info_request`. Each answer carries free-text and/or structured data.      |
| `acknowledgement`  | Receipt-only signal with `body.acknowledges_message_id`.                                      |

## Common envelope

Every message has this shape. Field-level details are in [`SPEC.md`](https://github.com/sudhanshuheda/loop/blob/main/SPEC.md).

```json
{
  "loop_version":   "0.1",
  "message_type":   "rfq | quote | po | decline | info_request | info_provided | acknowledgement",
  "message_action": "rfq_initial | rfq_modification | rfq_addition | quote_provided | info_request | info_provided | acknowledgement | award | cancel | other",
  "message_id":     "<uuid v4>",
  "thread_id":      "<uuid v4>",
  "in_reply_to":    "<uuid v4, optional>",
  "issued_at":      "<RFC 3339 timestamp>",
  "issuer":         { "org_name": "...", "email": "...", "contact_name": "...", "phone": "...", "address": {...}, "tax_id": {...}, "identifiers": {...} },
  "issuer_role":    "consignee | forwarder_requesting_quote | forwarder_providing_quote | shipper | carrier | other",
  "recipients":     [ { "org_name": "...", "email": "..." } ],
  "subject":        "<string, optional>",
  "body":           { "...message-type-specific..." },
  "attachments":    [ { "filename": "...", "uri": "cid:...", "kind": "msds | spec_sheet | drawing | packing_list | commercial_invoice | photo | other" } ],
  "extraction_meta":{
    "extraction_confidence": 0.95,
    "data_completeness":     "complete | partial | missing",
    "missing_fields":        [ { "field": "extensions.freight.chargeable_weight", "reason": "..." } ],
    "extraction_reasoning":  "<free text>"
  }
}
```

## Install and run

Clone the repository and use the validator to confirm any message you build is well-formed.

```bash
git clone https://github.com/sudhanshuheda/loop.git
cd loop
make install     # creates .venv and installs jsonschema + referencing
make test        # validates every example + confirms negative cases reject
```

To validate a specific message file:

```bash
.venv/bin/python -c "
import json, sys
from jsonschema import Draft202012Validator
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012
from pathlib import Path

schemas = list(Path('schemas/v0.1').glob('*.schema.json'))
reg = Registry().with_resources([
    (p.name, Resource(contents=json.loads(p.read_text()), specification=DRAFT202012))
    for p in schemas
])

msg = json.loads(sys.stdin.read())
schema_path = Path('schemas/v0.1') / f'{msg[\"message_type\"]}.schema.json'
schema = json.loads(schema_path.read_text())
errors = list(Draft202012Validator(schema, registry=reg).iter_errors(msg))
print('OK' if not errors else '\n'.join(str(e.message) for e in errors))
" < your-message.json
```

## How to emit a Loop message (3 steps)

### 1. Build the JSON payload

Start from the matching example in [`examples/`](https://github.com/sudhanshuheda/loop/tree/main/examples) and edit the fields. The schemas reject anything malformed, so write what you know and let validation tell you what's missing.

Required fields on every message: `loop_version`, `message_type`, `message_action`, `message_id` (generate a UUID v4), `thread_id` (UUID v4 — same as `message_id` for the first message in a new thread), `issued_at` (RFC 3339 timestamp, UTC), `issuer`, `issuer_role`, `recipients` (at least one), `body` (shape depends on `message_type`).

For RFQs, `body` requires at least `title`, `quote_deadline`, and one `line_items[]` entry. Do not include `unit_price` or `rate_basis` on RFQ line items.

For quotes, every `line_items[]` entry MUST have `unit_price` (a `Money` object) and `rate_basis` (one of `per_unit`, `per_kg`, `per_cbm`, `per_container`, `per_shipment`, `all_in`, `other`).

### 2. Build the MIME email

```
From: <issuer.email>
To: <recipients[0].email>
Subject: <envelope.subject>
Message-ID: <<envelope.message_id>@<your domain>>
X-Loop-Version: 0.1
X-Loop-Message-Type: <envelope.message_type>
X-Loop-Message-Action: <envelope.message_action>
X-Loop-Message-Id: <envelope.message_id>
X-Loop-Thread-Id: <envelope.thread_id>
MIME-Version: 1.0
Content-Type: multipart/mixed; boundary="loop-outer"

--loop-outer
Content-Type: text/plain; charset=utf-8

<human-readable rendering of the message>

--loop-outer
Content-Type: application/vnd.loop+json; version=0.1
Content-Disposition: attachment; filename="procurement.json"

<the JSON payload from step 1>

--loop-outer--
```

The human-readable `text/plain` part is REQUIRED. Suppliers without Loop support read this. Do not skip it.

### 3. Send it

Through any SMTP-compatible transport. Nylas, Microsoft Graph, Gmail API, plain SMTP — all work. Nothing in Loop is transport-specific beyond the MIME structure above.

## How to parse an inbound Loop message (4 steps)

1. **Detect.** If the email has an `X-Loop-Version` header OR an attachment with media type `application/vnd.loop+json`, treat it as Loop.
2. **Extract.** Prefer the attachment. Optional fallback: the email body MAY contain a fenced block between `---LOOP-BEGIN v=0.1---` and `---LOOP-END---` if attachments were stripped.
3. **Validate.** Run the JSON through the schema for the declared `message_type` (see `schemas/v0.1/<message_type>.schema.json`). Reject and surface to a human if validation fails.
4. **Trust check.** Confirm the envelope `issuer.email` matches the DKIM-aligned `From:` header. Reject or quarantine mismatches.

After parsing, the `thread_id` is your canonical conversation identifier. The `in_reply_to` field points at the specific prior message a reply targets. `message_action` tells you what kind of action the sender intends — route accordingly.

## Freight extension (the v0.1 reference vertical)

If you handle freight RFQs, `body.extensions.freight` carries everything you need:

- `mode`: `air | sea | road | rail | multimodal`
- `offer_direction`: `import | export | cross_trade | internal_transfer`
- `sea_freight_type`: `FCL | LCL` (sea mode only)
- `service_type`: `port_to_port | door_to_door | door_to_port | port_to_door`
- `origin`, `destination`: `Address` objects with UN/LOCODE `port_code`
- `incoterms` + `incoterms_place`: Incoterms 2020 codes (normalize deprecated codes — DDU→DAP, DAT→DPU)
- `ready_date`, `delivery_by`: ISO 8601 dates
- `commodity`, `hs_code`, `hts_code`, `cargo_type` (`general | hazardous | chilled | frozen | rolls | special_temperature`)
- `pieces`, `gross_weight`, `chargeable_weight`, `volume` (all `Quantity` objects with canonical UN/CEFACT units: `KGM`, `MTQ`, `CMT`, `EA`, `PLT`)
- `containers[]` (FCL): each `{ type, iso_type, count, is_reefer, is_open_top, is_flat_rack, in_gauge, stackable }`
- `packages[]` (LCL / air / road): each `{ kind, count, weight_each, dimensions, stackable, turnable, oversized }`
- `hazardous`: `{ is_hazardous, un_numbers[], class_numbers[], packing_groups[], proper_shipping_name, msds_attachment_refs[] }`
- `temperature_controlled`: `{ required, min_celsius, max_celsius, ventilation, shelf_life }`
- `restricted_items`: `{ has_restricted, kind, details }`
- `declared_value`, `commercial_invoice_value` (`Money` objects)
- `insurance`: `{ required, kind, covered_value }`
- `brokerage`: `{ required, side }` (`origin | destination | both`)
- `customs_filings`: `{ expected: ["shipping_bill_in", "boe_in", "acas_us", "ams_us", "isf_us", "ens_eu", "aes_us"] }`
- `carrier_preference[]`, `preferred_route`, `known_shipper` (`pax | cao | unknown`)
- `carrier`, `carrier_routing`, `vessel`, `transit_time` (quote-side fields)
- `consignee`, `shipper`, `notify_party` (`Party` objects)

Full reference: [`docs/extensions/freight.md`](https://github.com/sudhanshuheda/loop/blob/main/docs/extensions/freight.md).

## Canonical units (do not deviate)

| Concept     | Unit    | Notes                                  |
| ----------- | ------- | -------------------------------------- |
| Weight      | `KGM`   | Kilograms. Never lbs.                  |
| Volume      | `MTQ`   | Cubic metres. Never cuft.              |
| Length      | `CMT`   | Centimetres. Never inches.             |
| Count       | `EA`    | Each / pieces.                         |
| Pallet count| `PLT`   | Pallets.                               |
| Currency    | ISO 4217 | e.g. `USD`, `EUR`, `INR`. Always 3 uppercase letters. |
| Country     | ISO 3166-1 alpha-2 | e.g. `IN`, `DE`, `US`. Always 2 uppercase letters. |
| Port codes  | UN/LOCODE | e.g. `INNSA`, `AEJEA`, `BLR`, `FRA`. |
| Container types | ISO 6346 size/type codes preferred | e.g. `45G1`. Short names (`40HC`, `20GP`) also accepted. |

Monetary amounts and all dimensional values are **strings of decimal digits**, never floats. `"1.85"` not `1.85`. This avoids IEEE 754 precision corruption on round-trip.

## Repository layout

Everything you need is in [`sudhanshuheda/loop`](https://github.com/sudhanshuheda/loop):

```
README.md                            — repo-root overview
SPEC.md                              — normative v0.1 specification
CHANGELOG.md                         — version history
CONTRIBUTING.md                      — how to contribute
LICENSE                              — Apache-2.0
schemas/v0.1/                        — JSON Schema 2020-12 files
  common.schema.json                 — envelope + shared types
  rfq.schema.json
  quote.schema.json
  po.schema.json
  decline.schema.json
  info_request.schema.json
  info_provided.schema.json
  acknowledgement.schema.json
examples/                            — 9 worked example messages
  freight-rfq.json, freight-quote.json, freight-po.json, freight-decline.json
  fcl-sea-rfq.json
  hazmat-air-rfq.json
  services-rfp.json
  clarification-info-request.json, clarification-info-provided.json
bindings/email.md                    — MIME structure, headers, parsing rules
docs/
  why-agentic.md                     — what the design optimizes for
  design-principles.md
  extensions/freight.md              — full freight extension reference
  comparison.md                      — vs EDI / cXML / UBL / Peppol
  roadmap.md
tools/
  validate.py                        — positive validator
  validate_negative.py               — negative validator
  requirements.txt
```

## What changed from prior procurement standards

Loop is small on purpose. The core spec is ~600 lines because previous standards (UBL, Peppol, cXML, EDI, RosettaNet, ebXML) failed not from missing features but from being too large to adopt outside government-mandated zones. Loop's bet is that small + agent-first + extensible beats comprehensive + committee-driven + XML.

If you are deciding whether to add Loop support: emit-only is a real contribution, parse-only is a real contribution. You do not need to do both to benefit. The network effect compounds as participants come online.

## Where to ask questions

- File an issue: <https://github.com/sudhanshuheda/loop/issues/new>
- Open a PR: <https://github.com/sudhanshuheda/loop/pulls>
- Read the design notes: <https://github.com/sudhanshuheda/loop/blob/main/docs/why-agentic.md>

License: Apache-2.0. No patent traps, no SaaS-gated reference implementation, no vendor lock-in.
