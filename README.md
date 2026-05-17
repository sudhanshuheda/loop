# Loop — an open procurement format for agents

[![validate](https://github.com/sudhanshuheda/loop/actions/workflows/validate.yml/badge.svg)](https://github.com/sudhanshuheda/loop/actions/workflows/validate.yml)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](./LICENSE)
[![Status: Draft v0.1](https://img.shields.io/badge/status-draft%20v0.1-orange.svg)](./CHANGELOG.md)

A small, open JSON format for **machine-readable procurement** between buyers and suppliers. Designed so AI agents on either side can emit, parse, and negotiate procurement without scraping free-form emails.

Loop is shaped by one constraint: **the receiver is an agent, not a human.** Every field name, every enum, every required boundary exists to make an LLM on the other side do less work and make fewer mistakes.

---

## The problem

Today, procurement moves like this:

1. A buyer captures a request in their procurement tool (Coupa, Ariba, GEP, an ERP, or a homegrown spreadsheet).
2. The tool emits a **PDF or a free-form email** and the buyer sends it to suppliers.
3. The supplier — increasingly, a supplier's **AI agent** — has to re-extract that data from prose, tables, and attachments, often losing structure along the way.
4. The supplier replies with another free-form email, and the buyer's agent re-extracts that too.

This is lossy at every hop. Every vendor reinvents the same extraction layer. Every quote-vs-RFQ comparison is fuzzy because units, currencies, incoterms, and line-item identities don't survive the round trip.

**Loop fixes this by defining one tiny standard payload that rides alongside the human email.** Agents read the payload. Humans read the email. No scraping required.

## Why now

Email-based procurement has been the standard since the early 2000s. UBL, Peppol, cXML, and EDI have all tried to replace it; only the e-invoicing mandates have stuck. What's new in 2026 is that the receiving party is no longer a human reading prose — it's an LLM that hates parsing prose. Suppliers' AI vendors have a direct unit-economics reason to adopt a structured format: every parsed Loop email saves several extraction LLM calls. That alone is enough to drive adoption past the threshold previous standards never crossed.

## Design principles

1. **Email-native, not API-only.** Email is the universal B2B transport. Loop is designed to be embedded in email today.
2. **Human-readable fallback is mandatory.** Every Loop message ships alongside a human-readable rendering. Suppliers without Loop support see a normal email.
3. **Agent-first, not EDI-redux.** Field names are LLM-friendly English. No 4-character segment codes.
4. **Tiny core, namespaced extensions.** The core spec covers what every procurement message needs. Vertical specifics (freight modes, SaaS metering, capex specs) live in namespaced `extensions.*` blocks.
5. **Backwards-compatible additions.** Unknown fields MUST be preserved on round-trip. Agents MUST ignore fields they don't understand.
6. **No vendor lock-in.** No required identifiers issued by any company. Email address is the v0.1 identity primitive; DIDs and other identifiers can be layered in later.

## What's in v0.1

| Message           | Direction        | Purpose                                                       |
| ----------------- | ---------------- | ------------------------------------------------------------- |
| `rfq`             | Buyer → Supplier | Request a quote (initial, modification, or addition)          |
| `quote`           | Supplier → Buyer | Respond with priced line items                                |
| `po`              | Buyer → Supplier | Award and confirm purchase                                    |
| `decline`         | Either           | Decline politely with a reason code                           |
| `info_request`    | Either           | Ask for missing information, bound to specific fields         |
| `info_provided`   | Either           | Answer an `info_request`                                      |
| `acknowledgement` | Either           | Lightweight "received, no action" signal                      |

Plus: a common envelope (with `message_action`, `issuer_role`, and optional `extraction_meta` for agents to self-declare confidence), shared types (`Party`, `Money`, `Address`, `LineItem`, `Timeframe`, `OperationalFlags`), and one worked vertical extension — `extensions.freight` — that covers air / sea / road / rail.

Out of scope for v0.1, planned for later: counter-quotes, amendments, invoices, shipment events, signed payloads.

## Quick example

A freight buyer's agent emits an air-freight RFQ. It arrives in the supplier's inbox as a normal email **plus** a `procurement.json` attachment containing:

```json
{
  "loop_version":   "0.1",
  "message_type":   "rfq",
  "message_action": "rfq_initial",
  "message_id":     "9c2a8b8e-2c1f-4f3a-9d2b-7a1d2a3f4e5d",
  "thread_id":      "9c2a8b8e-2c1f-4f3a-9d2b-7a1d2a3f4e5d",
  "issued_at":      "2026-05-17T09:00:00Z",
  "issuer": {
    "org_name":     "Acme Logistics Pvt Ltd",
    "contact_name": "Priya Shah",
    "email":        "priya@acme.example"
  },
  "issuer_role": "forwarder_requesting_quote",
  "recipients":  [{ "org_name": "BlueWing Freight", "email": "quotes@bluewing.example" }],
  "body": {
    "title":          "Air freight: BLR → FRA, 2 pallets electronics",
    "quote_deadline": "2026-05-19T12:00:00Z",
    "line_items": [
      { "id": "1", "description": "Electronics, palletized, non-hazardous",
        "quantity": { "value": "2", "unit": "PLT" } }
    ],
    "flags": {
      "cost_vs_time_preference": "balanced",
      "requested_quote_fields":  ["carrier", "transit_time", "validity"]
    },
    "extensions": {
      "freight": {
        "mode":              "air",
        "offer_direction":   "export",
        "service_type":      "port_to_port",
        "origin":            { "country": "IN", "city": "Bengaluru",        "port_code": "BLR" },
        "destination":       { "country": "DE", "city": "Frankfurt am Main","port_code": "FRA" },
        "incoterms":         "FCA",
        "incoterms_place":   "Bengaluru",
        "ready_date":        "2026-05-22",
        "commodity":         "Electronics, palletized",
        "cargo_type":        "general",
        "gross_weight":      { "value": "850",  "unit": "KGM" },
        "chargeable_weight": { "value": "1100", "unit": "KGM" },
        "volume":            { "value": "1.74", "unit": "MTQ" },
        "hazardous":         { "is_hazardous": false }
      }
    }
  },
  "extraction_meta": { "extraction_confidence": 0.95, "data_completeness": "complete" }
}
```

The supplier's agent parses this directly — no email scraping, no PDF table extraction, no unit guessing. It replies with a `quote` message in the same shape. See [`examples/`](./examples) for the full thread (`rfq → quote → po`), a clarification pair (`info_request → info_provided`), and worked examples for FCL sea, hazmat air, and a non-freight services RFP.

## Repository layout

```
.
├── README.md            ← you are here
├── SPEC.md              ← the formal v0.1 specification
├── CHANGELOG.md
├── LICENSE              ← Apache-2.0
├── CONTRIBUTING.md
├── Makefile             ← make install / make test
├── schemas/v0.1/        ← JSON Schema 2020-12 files
├── examples/            ← realistic end-to-end message examples
├── bindings/            ← transport bindings (email today, more later)
├── docs/                ← design rationale, comparisons, roadmap, extensions
├── tools/               ← validator scripts + requirements
└── .github/             ← CI workflow + issue / PR templates
```

## Getting started

Read the documents in this order:

1. **[SPEC.md](./SPEC.md)** — the v0.1 specification (envelope, message types, common types, extensions).
2. **[docs/why-agentic.md](./docs/why-agentic.md)** — what we learned grounding the design against a production agentic procurement pipeline.
3. **[docs/extensions/freight.md](./docs/extensions/freight.md)** — the reference vertical extension.
4. **[bindings/email.md](./bindings/email.md)** — how to ship Loop over plain email.
5. **[docs/comparison.md](./docs/comparison.md)** — how Loop differs from EDI / cXML / UBL / Peppol.
6. **[docs/roadmap.md](./docs/roadmap.md)** — what's planned beyond v0.1.

## Validating

Loop messages are validated with standard JSON Schema 2020-12 tooling. Any validator works — `ajv`, `jsonschema` (Python), `gojsonschema`, etc.

This repo ships a Python validator under `tools/`:

```bash
make install          # one-time: creates .venv and installs jsonschema + referencing
make test             # validates every example + confirms negative cases reject
```

You can also run validators independently:

```bash
make validate           # positive: every example validates against its schema
make validate-negative  # negative: malformed inputs are correctly rejected
```

Both run automatically on every pull request via [`.github/workflows/validate.yml`](./.github/workflows/validate.yml).

## Adoption

Loop aims to become the obvious default for agent-to-agent procurement — not literally universal, but the format any new AI procurement company reaches for first. Concrete ways to help that happen:

- **Build an SDK** in your favorite language. Type-safe parser + emitter generated from the JSON Schemas.
- **Add Loop support to your agent.** Emit on outbound replies, parse when present on inbound. Both ends benefit even if only one is doing it.
- **Bring a new vertical.** Propose an `extensions.<vertical>` block for SaaS, capex, services, healthcare, real estate — whichever procurement you live in.
- **Ship a binding.** v0.1 covers email. Webhook, MCP server, and Slack bindings are open.
- **Send real examples.** PII-scrubbed examples from real procurement traffic are the single most useful contribution.

See [CONTRIBUTING.md](./CONTRIBUTING.md) for the development setup and PR conventions.

## License

[Apache-2.0](./LICENSE). No patent traps, no SaaS-gated reference implementation, no vendor lock-in.
