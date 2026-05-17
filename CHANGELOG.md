# Changelog

All notable changes to Loop will be documented here. Format follows [Keep a Changelog](https://keepachangelog.com/), versioning follows the rules in [`SPEC.md` §8](./SPEC.md#8-versioning).

## [0.1.0] — 2026-05-17 (Draft)

Initial draft. Grounded against a production agentic procurement pipeline; see [`docs/why-agentic.md`](./docs/why-agentic.md) for the design notes.

### Added — envelope

- `message_action` enum (`rfq_initial`, `rfq_modification`, `rfq_addition`, `quote_provided`, `info_request`, `info_provided`, `acknowledgement`, `award`, `cancel`, `other`).
- `issuer_role` enum (`consignee`, `forwarder_requesting_quote`, `forwarder_providing_quote`, `shipper`, `carrier`, `other`).
- Optional `extraction_meta` block (`extraction_confidence`, `data_completeness`, `missing_fields`, `extraction_reasoning`) so emitting agents can self-declare confidence.

### Added — message types

- `info_request` — clarification questions bound to specific `field_path`s, with `required` flag per question.
- `info_provided` — answers to a prior `info_request`. Each answer carries free-text, structured, or attachment-reference content.
- `acknowledgement` — receipt-only signal.

### Added — common types

- `rate_basis` enum on `LineItem` (`per_unit`, `per_kg`, `per_cbm`, `per_container`, `per_shipment`, `all_in`, `other`). Required on priced line items (quote, PO). Forbidden on RFQ line items.
- `OperationalFlags` block for non-customer-facing signals (`time_sensitive`, `cost_vs_time_preference`, `requested_quote_fields`, `sender_company_type`, `carrier_preference`, `preferred_route`).
- `TransitTime` type (`min_days`, `max_days`, `notes`) on quotes.
- `Attachment.kind` enum hint (`spec_sheet`, `drawing`, `msds`, `packing_list`, `commercial_invoice`, `photo`, `other`).
- `end_customer` field on RFQ body for the relay case (forwarder issuing on behalf of a downstream consignee).

### Added — freight extension

Expanded to cover the full surface area of a real agentic freight pipeline:

- `offer_direction` (import / export / cross_trade / internal_transfer).
- `sea_freight_type` (FCL / LCL), `service_type` (port_to_port / door_to_door / door_to_port / port_to_door).
- `cargo_type` enum (general / hazardous / chilled / frozen / rolls / special_temperature) and free-form `commodity_attributes` block for vertical-of-a-vertical SOP flags.
- Full `hazardous` block (UN numbers[], class numbers[], packing groups[], proper shipping name, MSDS attachment refs).
- Full `temperature_controlled` block (min/max celsius, ventilation, shelf life).
- `restricted_items` block (live animals, religious texts, lighters, hand-carry-only).
- `containers[]` (typed by short name + optional ISO 6346 code, with reefer / open-top / flat-rack flags) and `packages[]` (LCL / air / road palletized).
- `declared_value`, `commercial_invoice_value`, `insurance` (clause_a / clause_c), `brokerage` (origin / destination / both), `customs_filings.expected` (shipping_bill_in, boe_in, acas_us, ams_us, isf_us, ens_eu, aes_us).
- `target_rate`, `carrier_preference[]`, `preferred_route`, `known_shipper` (pax / cao / unknown).
- `carrier`, `carrier_routing`, `vessel`, `transit_time` on the quote-side block.
- Mode-specific guidance for air / sea / road / rail / multimodal.

### Added — schemas

- JSON Schema 2020-12 for all seven message types and the common envelope.
- `LineItemUnpriced` rule forbids both `unit_price` and `rate_basis` on RFQ.
- `LineItemPriced` rule requires both on quote and PO.

### Added — bindings

- Email reference binding (`bindings/email.md`): MIME structure, `X-Loop-*` headers, optional fenced-block in-body fallback, inbound parsing rules.

### Added — docs

- `docs/why-agentic.md` — what we learned grounding the design against a production pipeline.
- `docs/extensions/freight.md` — full reference for the freight vertical.
- `docs/design-principles.md`, `docs/comparison.md` (vs EDI / cXML / UBL / Peppol), `docs/roadmap.md`.

### Added — examples

- `freight-rfq.json` → `freight-quote.json` → `freight-po.json` (air export thread).
- `freight-decline.json` (capacity decline with alternative proposal).
- `services-rfp.json` (non-freight RFP, validates same envelope).
- `fcl-sea-rfq.json` (full container load, DAP terms, brokerage required at destination).
- `hazmat-air-rfq.json` (UN3480 Li-ion batteries with MSDS attachment, ACAS filing flagged).
- `clarification-info-request.json` → `clarification-info-provided.json` (machine-bound Q&A round).

### Verified

- All 9 examples validate against their schemas.
- 14 negative test cases (forbidden fields, missing required fields, out-of-range values, wrong enums) correctly fail validation.
