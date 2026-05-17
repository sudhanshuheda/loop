# Loop Specification — v0.1 (Draft)

**Loop** — an open procurement format for agents.
Status: Draft · Last updated: 2026-05-17

The keywords **MUST**, **MUST NOT**, **SHOULD**, **SHOULD NOT**, and **MAY** in this document are to be interpreted as described in RFC 2119.

---

## 1. Overview

Loop is a JSON-based message format for procurement communication between independent organizations. Every Loop message is a self-contained JSON object that carries:

- An **envelope** identifying the message, its participants, and the conversational intent.
- A typed **body** whose shape is determined by `message_type`.
- Optional namespaced **extensions** for vertical-specific data.

Messages are transported over a binding (email is the v0.1 reference binding). The format itself is transport-agnostic.

The spec was designed alongside a production agentic procurement pipeline (Sidecar RFQ). Section [§10](#10-what-this-spec-optimizes-for) describes which pipeline pain points each design choice eliminates.

## 2. Conformance

An implementation is **conformant** if it:

1. Produces messages that validate against the JSON Schemas in [`schemas/v0.1/`](./schemas/v0.1/).
2. Preserves unknown fields when relaying or storing messages.
3. Ignores unknown fields without erroring when parsing.
4. Implements at least one transport binding (email is the reference binding for v0.1).

## 3. Envelope

Every Loop message MUST have the following top-level structure:

```json
{
  "loop_version":   "0.1",
  "message_type":   "rfq | quote | po | decline | info_request | info_provided | acknowledgement",
  "message_action": "rfq_initial | rfq_modification | rfq_addition | quote_provided | info_request | info_provided | acknowledgement | award | cancel | other",
  "message_id":     "<uuid>",
  "thread_id":      "<uuid>",
  "in_reply_to":    "<uuid, optional>",
  "issued_at":      "<RFC 3339 timestamp>",
  "issuer":         { "...": "Party" },
  "issuer_role":    "consignee | forwarder_requesting_quote | forwarder_providing_quote | shipper | carrier | other",
  "recipients":     [ { "...": "Party" } ],
  "subject":        "<string, optional>",
  "body":           { "...": "type-specific" },
  "attachments":    [ { "...": "Attachment" } ],
  "extraction_meta":{ "...": "ExtractionMeta, optional" }
}
```

### 3.1 Envelope fields

| Field             | Type            | Required | Notes                                                             |
| ----------------- | --------------- | -------- | ----------------------------------------------------------------- |
| `loop_version`    | string          | yes      | Semver-ish. v0.1 messages MUST set `"0.1"`.                       |
| `message_type`    | string          | yes      | Format shape. See §5.                                             |
| `message_action`  | string          | yes      | Conversational intent. Lets receivers route without re-classifying. See §3.3. |
| `message_id`      | UUID v4         | yes      | Globally unique per message.                                      |
| `thread_id`       | UUID v4         | yes      | Same across all messages in one procurement conversation.         |
| `in_reply_to`     | UUID v4         | no       | `message_id` of the message being responded to.                   |
| `issued_at`       | RFC 3339        | yes      | Wall-clock time the message was emitted (UTC strongly preferred). |
| `issuer`          | Party           | yes      | Sending organization + contact.                                   |
| `issuer_role`     | enum            | yes      | The sender's role in the procurement (see §3.4).                  |
| `recipients`      | Party[]         | yes      | At least one recipient.                                           |
| `subject`         | string          | no       | Optional human-readable subject. SHOULD mirror the email subject when emailed. |
| `body`            | object          | yes      | Shape depends on `message_type`.                                  |
| `attachments`     | Attachment[]    | no       | Pointers to additional files.                                     |
| `extraction_meta` | ExtractionMeta  | no       | Self-declared confidence and completeness (§4.8). Strongly encouraged on agent-emitted messages. |

### 3.2 Thread semantics

- A new RFQ starts a thread; `message_id` and `thread_id` MAY be equal.
- All subsequent messages MUST reuse the original `thread_id`.
- Recipients of an RFQ that fans out to multiple suppliers each spawn their own response stream within the same `thread_id`. Implementations distinguish replies by `in_reply_to` and `issuer`.

### 3.3 `message_action` vocabulary

`message_type` describes the **format shape**. `message_action` describes the **conversational intent**. Both are necessary because the same shape (`rfq`) means very different things to a receiving agent:

| `message_action`     | Meaning                                                                       |
| -------------------- | ----------------------------------------------------------------------------- |
| `rfq_initial`        | First request in a new thread. Receiver should produce a fresh quote.         |
| `rfq_modification`   | Changes to a previously-sent RFQ. Receiver should update prior quote.         |
| `rfq_addition`       | Adds line items to a previously-sent RFQ. Receiver should price the additions.|
| `quote_provided`     | A priced quote response.                                                      |
| `info_request`       | The sender needs more information before they can proceed.                    |
| `info_provided`      | The sender is answering a previous `info_request`.                            |
| `acknowledgement`    | Receipt-only message; no action required.                                     |
| `award`              | Buyer is awarding the business (PO typically follows).                        |
| `cancel`             | Cancellation of an open RFQ or PO.                                            |
| `other`              | Anything else; senders SHOULD prefer a specific value.                        |

The valid pairs of (`message_type`, `message_action`) are listed in [`schemas/v0.1/common.schema.json`](./schemas/v0.1/common.schema.json).

### 3.4 `issuer_role` vocabulary

Procurement conversations have stable roles. Declaring the sender's role lets receiving agents route without inferring it from prose:

| Role                            | Notes |
| ------------------------------- | ----- |
| `consignee`                     | The end buyer / cargo owner.                                                 |
| `forwarder_requesting_quote`    | Freight forwarder soliciting rates from carriers/co-loaders/other forwarders. |
| `forwarder_providing_quote`     | Freight forwarder quoting back to a customer.                                |
| `shipper`                       | The party physically tendering cargo at origin (when distinct from consignee).|
| `carrier`                       | Airline / shipping line / NVOCC / trucker / rail operator.                   |
| `other`                         | Anything not covered.                                                        |

## 4. Common types

### 4.1 Party

```json
{
  "org_name":     "Acme Logistics Pvt Ltd",
  "contact_name": "Priya Shah",
  "email":        "priya@acme.example",
  "phone":        "+91-99-1234-5678",
  "address":      { "...": "Address" },
  "tax_id":       { "kind": "GSTIN", "value": "29ABCDE1234F1Z5" },
  "identifiers":  { "duns": "123456789", "iec": "0712345678" }
}
```

| Field          | Type    | Required | Notes |
| -------------- | ------- | -------- | ----- |
| `org_name`     | string  | yes      | Legal or trading name. |
| `contact_name` | string  | no       | Individual contact. |
| `email`        | string  | yes      | Primary email. Identity primitive in v0.1. |
| `phone`        | string  | no       | E.164 preferred. |
| `address`      | Address | no       |       |
| `tax_id`       | object  | no       | `{ kind, value }` — `kind` free-form (`"GSTIN"`, `"VAT"`, `"EIN"`, `"IEC"`, …). |
| `identifiers`  | object  | no       | Map of `<scheme>: <value>`. |

### 4.2 Address

```json
{
  "country":     "IN",
  "region":      "Karnataka",
  "city":        "Bengaluru",
  "postal_code": "560100",
  "street":      "Plot 42, Whitefield",
  "port_code":   "BLR"
}
```

`country` is required and uses ISO 3166-1 alpha-2. `port_code` uses UN/LOCODE.

### 4.3 Money

```json
{ "amount": "1250.00", "currency": "USD" }
```

`amount` is a decimal string (no float-precision corruption). `currency` is ISO 4217.

### 4.4 Quantity

```json
{ "value": "850", "unit": "KGM" }
```

`value` is a decimal string. `unit` SHOULD be a UN/CEFACT Recommendation 20 code (`KGM`, `MTQ`, `EA`, `PLT`, `CBM`, `CMT`, `MTR`, …). Free-form strings are allowed but discouraged.

Recommended canonical units for freight:

| Concept         | Unit code | Notes                          |
| --------------- | --------- | ------------------------------ |
| Weight          | `KGM`     | Kilograms.                     |
| Volume          | `MTQ`     | Cubic metres.                  |
| Length          | `CMT`     | Centimetres.                   |
| Count           | `EA`      | Each / pieces.                 |
| Pallet count    | `PLT`     | Pallets.                       |
| Container count | `EA`      | Use `extensions.freight.container_plan` for typed containers. |

Senders MUST NOT send weights in pounds, volumes in cubic feet, or lengths in inches unless the receiver has explicitly opted in to alternate units. The format trades emitter convenience for receiver clarity.

### 4.5 Timeframe

```json
{
  "ready_date":  "2026-05-22",
  "required_by": "2026-05-30",
  "valid_until": "2026-05-19T12:00:00Z"
}
```

All fields optional; meaning depends on context.

### 4.6 LineItem

```json
{
  "id":          "1",
  "description": "Stainless steel bolt, M8 × 30mm, grade A2",
  "sku":         "BOLT-M8-30-A2",
  "quantity":    { "value": "5000", "unit": "EA" },
  "unit_price":  { "amount": "0.12", "currency": "USD" },
  "rate_basis":  "per_unit",
  "specs":       { "thread": "metric", "grade": "A2-70" },
  "notes":       "Prefer DIN 933"
}
```

| Field        | Required | Notes |
| ------------ | -------- | ----- |
| `id`         | yes      | Stable within a message. Quotes MUST reuse RFQ line `id`s. |
| `description`| yes      | LLM-friendly free text. |
| `sku`        | no       | Internal or vendor SKU. |
| `quantity`   | yes      | What is being requested / quoted / purchased. |
| `unit_price` | conditional | Required on `quote` and `po`. MUST NOT be present on `rfq`. |
| `rate_basis` | conditional | Required on `quote` and `po`. See §4.7. |
| `specs`      | no       | Free-form structured attributes. |
| `notes`      | no       |       |

### 4.7 `rate_basis` vocabulary

How a `unit_price` is being applied. Receivers MUST NOT assume — senders MUST declare.

| Value            | Meaning                                                                  |
| ---------------- | ------------------------------------------------------------------------ |
| `per_unit`       | Price × `quantity.value` (when `quantity.unit` is `EA` or similar).      |
| `per_kg`         | Price × chargeable / gross weight in kilograms.                          |
| `per_cbm`        | Price × volume in cubic metres.                                          |
| `per_container`  | Flat per container; `quantity` is the number of containers.              |
| `per_shipment`   | Flat per shipment; `quantity.value` SHOULD be `"1"`.                     |
| `all_in`         | Single total for the line item regardless of `quantity` math.            |
| `other`          | Anything else; senders SHOULD prefer a specific value and explain in `notes`. |

### 4.8 ExtractionMeta

Optional envelope-level block that lets an emitting agent self-declare its confidence. Receivers MAY use this to route messages with low confidence to a human review queue without re-running their own classifier.

```json
{
  "extraction_confidence": 0.78,
  "data_completeness":     "complete | partial | missing",
  "missing_fields": [
    { "field": "extensions.freight.chargeable_weight", "reason": "Volumetric weight not provided; gross weight only." }
  ],
  "extraction_reasoning":  "Inferred FCL from '2x40HC'. Pickup address not specified — left null."
}
```

| Field                  | Type    | Notes |
| ---------------------- | ------- | ----- |
| `extraction_confidence`| number  | 0.0–1.0. Self-reported. |
| `data_completeness`    | enum    | `complete` / `partial` / `missing`. |
| `missing_fields`       | array   | Each `{ field, reason }`. `field` is a dotted path within the body or extensions. |
| `extraction_reasoning` | string  | Free-form short explanation. |

### 4.9 Attachment

```json
{
  "filename":    "spec-sheet.pdf",
  "media_type":  "application/pdf",
  "size_bytes":  142053,
  "sha256":      "a1b2c3...",
  "uri":         "cid:spec-sheet-0",
  "description": "Mechanical drawing rev B",
  "kind":        "spec_sheet | drawing | msds | packing_list | commercial_invoice | photo | other"
}
```

`kind` is an optional hint to the receiver about what the attachment represents.

### 4.10 Terms

Free-form, with conventional keys. Implementations SHOULD prefer these keys when applicable:

- `payment_terms` (string, e.g. `"Net 30"`)
- `incoterms` (string, Incoterms 2020 — see §6 for normalization)
- `warranty`, `sla`, `cancellation`, `late_fee`

Verticals may define additional conventional keys in their extension documentation.

## 5. Message types

### 5.1 `rfq` — Request for Quote

```json
{
  "title":               "...",
  "description":         "...",
  "quote_deadline":      "2026-05-19T12:00:00Z",
  "validity_required":   "P14D",
  "currency_preference": "USD",
  "line_items":          [ { "...": "LineItem (no unit_price, no rate_basis)" } ],
  "end_customer":        { "...": "Party (optional, when issuer is a forwarder relaying)" },
  "flags":               { "...": "OperationalFlags, optional" },
  "terms":               { "...": "Terms" },
  "extensions":          { "...": "namespaced" }
}
```

| Field                | Required | Notes |
| -------------------- | -------- | ----- |
| `title`              | yes      | Short human-readable title. |
| `description`        | no       | Free-form narrative context. |
| `quote_deadline`     | yes      | RFC 3339. |
| `validity_required`  | no       | ISO 8601 duration (e.g. `P14D`). |
| `line_items`         | yes      | ≥1 unpriced item. |
| `currency_preference`| no       | ISO 4217 hint. |
| `end_customer`       | no       | When `issuer_role` is `forwarder_requesting_quote` and the issuer is acting on behalf of a downstream consignee. Improves agent-side identity disambiguation. |
| `flags`              | no       | Operational signals — see §5.6. |
| `terms`              | no       |       |
| `extensions`         | no       | Vertical specifics. |

### 5.2 `quote` — Quote response

```json
{
  "rfq_message_id": "<uuid>",
  "validity":   { "valid_until": "2026-05-26T23:59:59Z" },
  "line_items": [ { "...": "LineItem (with unit_price + rate_basis)" } ],
  "subtotal":   { "...": "Money" },
  "charges":    [ { "label": "Fuel surcharge", "amount": { "...": "Money" } } ],
  "taxes":      [ { "label": "GST 18%",        "amount": { "...": "Money" } } ],
  "total":      { "...": "Money" },
  "transit_time": { "min_days": 3, "max_days": 5, "notes": "subject to space" },
  "carrier":      "Lufthansa Cargo",
  "terms":      { "...": "Terms" },
  "notes":      "...",
  "extensions": { "...": "namespaced" }
}
```

| Field            | Required | Notes |
| ---------------- | -------- | ----- |
| `rfq_message_id` | yes      | The RFQ being responded to. Also set envelope `in_reply_to`. |
| `validity`       | yes      | Must have at least `valid_until`. |
| `line_items`     | yes      | Each MUST reuse RFQ line `id`s. New ids allowed for supplier-proposed alternatives. |
| `subtotal`       | yes      |       |
| `charges`        | no       | Surcharges (fuel, security, handling, expedite, etc.). |
| `taxes`          | no       |       |
| `total`          | yes      |       |
| `transit_time`   | no       | Strongly encouraged for freight. |
| `carrier`        | no       | Naming the carrier the quote is built against. |
| `terms`          | no       |       |
| `notes`          | no       |       |
| `extensions`     | no       |       |

All `Money` fields in one quote SHOULD share `currency`. Agents MUST NOT auto-sum across currencies.

### 5.3 `po` — Purchase Order

```json
{
  "po_number":        "ACME-2026-00421",
  "quote_message_id": "<uuid>",
  "line_items":       [ { "...": "LineItem (priced)" } ],
  "subtotal":         { "...": "Money" },
  "charges":          [ "..." ],
  "taxes":            [ "..." ],
  "total":            { "...": "Money" },
  "delivery": {
    "ship_to":     { "...": "Address" },
    "bill_to":     { "...": "Address" },
    "required_by": "2026-05-30"
  },
  "terms":      { "...": "Terms" },
  "notes":      "...",
  "extensions": { "...": "namespaced" }
}
```

| Field              | Required | Notes |
| ------------------ | -------- | ----- |
| `po_number`        | yes      | Buyer's PO number. |
| `quote_message_id` | no       | Reference if accepting a quote. Direct-issued POs MAY omit. |
| `line_items`       | yes      |       |
| `subtotal`/`total` | yes      |       |
| `delivery`         | yes      | At least `ship_to` is required. |
| `terms`            | no       |       |

A supplier acknowledges a PO with `message_type: acknowledgement` (or echoes the `po` back), or rejects it with a `decline`.

### 5.4 `decline` — Decline

```json
{
  "declines_message_id": "<uuid>",
  "reason_code":         "no_capacity | out_of_scope | price_unworkable | timing | lane_not_served | insufficient_info | restricted_commodity | other",
  "reason_text":         "...",
  "alternative_proposal": "..."
}
```

`reason_code` is the routable signal. `restricted_commodity` was added because freight pipelines specifically need to flag cargo categories they can't carry (e.g. living animals, religious texts in certain origins, batteries by air without approval).

### 5.5 `info_request` and `info_provided` — Clarification

Two message types form a clarification pair.

`info_request` body:

```json
{
  "concerns_message_id": "<uuid>",
  "questions": [
    {
      "id":           "q1",
      "field_path":   "extensions.freight.chargeable_weight",
      "question":     "Could you provide chargeable weight or piece dimensions?",
      "required":     true
    },
    {
      "id":           "q2",
      "field_path":   "extensions.freight.hazardous.un_number",
      "question":     "Cargo description suggests batteries — please share the MSDS.",
      "required":     true
    }
  ]
}
```

`info_provided` body:

```json
{
  "in_reply_to_request": "<uuid>",
  "answers": [
    { "id": "q1", "answer_text": "Chargeable weight 1100 kg.", "structured": { "value": "1100", "unit": "KGM" } },
    { "id": "q2", "answer_text": "MSDS attached.", "attachment_ref": "cid:msds-0" }
  ]
}
```

| Field         | Notes |
| ------------- | ----- |
| `id`          | Stable within the conversation. Answers reuse `id`s. |
| `field_path`  | Dotted path inside the RFQ that this question targets. Lets a receiving agent merge the answer back into a single denormalized RFQ. |
| `required`    | Whether the receiver considers the field necessary to quote. |
| `structured`  | Optional machine-parseable answer. When present, it MUST match the type implied by `field_path` in the relevant schema. |
| `attachment_ref` | Optional reference to an attachment (by `cid:` or other URI) that contains the answer. |

### 5.6 `acknowledgement` — Receipt-only

```json
{
  "acknowledges_message_id": "<uuid>",
  "note": "Received, working on rates."
}
```

A lightweight signal for "got your message, no other action right now." Useful for read-receipt-style flows between agents.

### 5.7 OperationalFlags

Free-form-ish block of operational signals that the issuing agent **does not need the receiver to ask the user about**. These exist because real procurement pipelines have a layer of context that isn't part of the goods/services being procured but does shape how the request should be handled.

```json
{
  "time_sensitive":          true,
  "cost_vs_time_preference": "cost | time | balanced",
  "requested_quote_fields":  ["carrier", "transit_time", "validity"],
  "sender_company_type":     "customs_broker | freight_forwarder | manufacturer | trading_company | other",
  "carrier_preference":      "Maersk, Hapag-Lloyd preferred",
  "preferred_route":         "via Singapore transhipment OK"
}
```

All fields optional. Verticals MAY extend the flag set under `extensions.<vertical>.flags` to keep the core block stable.

## 6. Incoterms normalization

`terms.incoterms` and freight-extension incoterms fields SHOULD use Incoterms 2020 codes. Deprecated codes encountered in the wild SHOULD be normalized **before** validation per this table:

| Deprecated | Replacement |
| ---------- | ----------- |
| `DDU`      | `DAP`       |
| `DAF`      | `DAP`       |
| `DES`      | `DAP`       |
| `DEQ`      | `DPU`       |
| `DAT`      | `DPU`       |
| `DTD`      | `DAP` (where door-to-door semantics apply; emit `notes`) |

Senders MAY emit Incoterms-2010 codes when the receiver is known to accept them; receivers MUST normalize on ingest.

## 7. Extensions

Vertical specifics live under `body.extensions.<namespace>`. Examples:

- `extensions.freight` — air / sea / road / rail shipments. Reference v0.1 vertical, defined in [`docs/extensions/freight.md`](./docs/extensions/freight.md).
- `extensions.saas` — seats, metered usage, term length (planned).
- `extensions.capex` — depreciation class, installation requirements (planned).

Conformant agents MUST ignore extensions they don't understand and MUST preserve them on relay.

## 8. Versioning

- `loop_version` follows `MAJOR.MINOR`.
- **Minor** versions add only. Unknown fields are preserved.
- **Major** versions MAY break compatibility and require opt-in via transport-level signaling.

## 9. Security considerations (v0.1)

Loop v0.1 does not mandate signing or encryption. Email's existing protections (DKIM, SPF, DMARC, TLS in transit) provide the same trust surface as today's prose procurement emails — no worse, no better.

Future versions will add an optional JWS-signed envelope for non-repudiation, particularly for POs.

Agents consuming Loop messages MUST:

- Validate against schema before acting.
- Treat `issuer.email` as untrusted until verified against transport-level identity (e.g. DKIM-aligned `From` for the email binding).
- Bound the size and depth of `extensions` and `attachments` to prevent denial-of-service.
- Treat `extraction_meta.extraction_confidence` as advisory, not authoritative — do not skip schema validation based on a high reported confidence.

## 10. What this spec optimizes for

Six choices in v0.1 exist because production agentic procurement pipelines spend real engineering effort working around their absence. Each is a deliberate response:

1. **`issuer_role` + `message_action` on the envelope.** Routing decisions ("is this a fresh RFQ, a modification, a clarification?", "is the sender a forwarder or the end consignee?") happen at message intake. Without these fields receivers re-classify with an LLM call on every inbound message.

2. **`flags` block.** Production pipelines carefully separate fields they should ask the customer about from operational context they should record silently (sender company type, urgency, requested quote-field list, carrier preference). Without a structured flags block these leak into prose and the receiver re-extracts them every time.

3. **`extraction_meta`.** Agents on both sides need to know how much to trust the structured payload. A `0.7` confidence with a flagged missing field is far more actionable than a high-quality-looking JSON that omits the gap.

4. **Mandatory `rate_basis`.** Quote prices are routinely misinterpreted: $0.12 per_unit vs per_kg vs per_cbm are all plausible parses of "12 cents." Production pipelines have an entire LLM step (Sidecar's `AgentQuoteCheck.unit`) whose only job is to recover this from prose. Make it a typed field.

5. **Strict canonical units.** Without unit discipline, pipelines build coercion layers (kg ↔ lb, cbm ↔ cuft, cm ↔ in). Pushing canonical units onto the emitter eliminates an entire normalization layer.

6. **`end_customer` on RFQ + `info_request` / `info_provided` messages.** Real RFQs are forwarded ("Customer X sent me this, please quote"). Real quoting requires clarification rounds. Modeling these as first-class messages prevents agents from re-inventing them on top of free-form replies.

## 11. References

- JSON Schema 2020-12 — https://json-schema.org
- ISO 4217 currency codes
- ISO 3166-1 alpha-2 country codes
- UN/LOCODE — port / airport / terminal codes
- UN/CEFACT Recommendation 20 — unit codes
- ISO 6346 — container size/type codes
- ISO 8601 / RFC 3339 — date and time formats
- Incoterms 2020 — ICC
- RFC 2119 — keywords for normative requirements
