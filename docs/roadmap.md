# Roadmap

Loop v0.1 deliberately scopes down. This is what's planned next.

## v0.2 — Negotiation completeness

- `clarification` message — request more info on an RFQ before quoting.
- `counter_quote` message — supplier proposes alternative line items / terms; buyer can accept or counter again.
- `amendment` message — modify a sent RFQ or PO without restarting the thread.
- `cancel` message — explicit thread termination with reason.
- An `award` message distinct from `po` for buyers who award without immediately issuing a PO.

## v0.3 — Trust

- Optional JWS-signed envelope for non-repudiation, especially on POs.
- Capability advertisement: `X-Loop-Accept` header for opt-in/version negotiation.
- A lightweight supplier directory format (publishable as `.well-known/loop.json`) for auto-discovery of preferred contact addresses, languages, and supported extensions.

## v0.4 — Operations after the PO

- Shipment events (`event_type`: booked, departed, arrived, delivered, exception).
- Invoice and credit note messages (or, more likely, recommended bridges to Peppol BIS / UBL invoicing rather than reimplementing).
- Payment status events.

## Vertical extensions in flight

- `extensions.freight` — included in v0.1 as the worked example. Continues to evolve in parallel with the core.
- `extensions.saas` — proposed for v0.2. Seats, metering, term length, true-up.
- `extensions.capex` — proposed for v0.2. Useful life, depreciation class, installation requirements.
- `extensions.services` — proposed for v0.2. Engagement type, deliverables, SLAs, data residency.

## Bindings

- Email (v0.1, reference binding).
- HTTPS webhook binding for two parties that both speak Loop and want lower latency than email round-trips.
- MCP binding — exposing inbound Loop messages as tool calls to procurement agents.

## Governance

Pre-1.0, the spec evolves in this repository. At 1.0 the intent is to move Loop to a vendor-neutral home (working group, foundation, or RFC track depending on what materializes), with the schema published at a stable `loop.org`-equivalent URL.

No fields or message types will be renamed or removed without a major version bump after 1.0.
