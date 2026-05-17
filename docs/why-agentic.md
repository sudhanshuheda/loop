# Why an "agentic" procurement format?

The "agentic" prefix is not branding. It names the specific user Loop was designed for: **an LLM-driven procurement agent on the receiving end of a B2B email**.

This document records what we learned from designing Loop alongside a production agentic procurement pipeline, and how each lesson shaped a concrete choice in the spec.

## What an agentic procurement pipeline actually does

To turn a freight RFQ email into something a quoting system can act on, a real pipeline does this:

1. **Pull** the inbound email out of the mailbox (Nylas / Gmail / Microsoft Graph).
2. **Classify** the email — RFQ vs modification vs clarification vs operational chatter — usually with an LLM call per message in the thread.
3. **Extract** a structured shipment record — mode, origin, destination, weights, volumes, container plan, incoterms, commodity, hazmat, insurance, etc. — again with an LLM call, often re-reading the entire thread to merge information that arrived across multiple emails.
4. **Validate** the record against SOP rules (required fields per mode, conditional fields per incoterm, hazmat-implies-MSDS, restricted-commodity blocking).
5. **Decide** whether to ask for clarification, draft a quote, or escalate to a human (HITL).
6. **Emit** the reply, which means turning structured data back into prose so the *other* side's pipeline can re-extract it.

Steps 2–4 collectively cost most of the LLM budget and most of the engineering effort. They exist entirely because the inbound message arrived as prose.

## What goes wrong, and what Loop does about it

### 1. Same message_type, different intent

A new RFQ, a modification, an addition, a clarification, and a generic acknowledgement are all routed differently by the receiver, but they often look indistinguishable on the wire. Real pipelines maintain a per-message `message_action` classifier just for this.

→ Loop puts `message_action` on the envelope. Receivers route in microseconds instead of an LLM call.

### 2. Who is the sender, really?

Procurement threads include consignees, forwarders requesting rates from other forwarders, forwarders relaying customer RFQs, carriers, and internal-team forwards. The right downstream behavior depends on which.

→ Loop puts `issuer_role` on the envelope, and adds `end_customer` to the RFQ body for the relay case where the issuer is a forwarder acting on a buyer's behalf.

### 3. Operational signals leak into prose

"Time-sensitive," "we'd prefer Maersk," "give me carrier + transit time + validity," "we're a customs broker, not the end customer" — these are operational signals the receiving agent should record but not ask the user about. In prose they get mixed up with the cargo description and re-extracted on every retry.

→ Loop puts these in a dedicated `flags` block (`time_sensitive`, `cost_vs_time_preference`, `requested_quote_fields`, `sender_company_type`, `carrier_preference`, `preferred_route`).

### 4. Quote rates are unparseable without `rate_basis`

`$1.85` is per kg, per CBM, per shipment, or all-in depending on context — and the context is in the prose around it. Real pipelines have an entire LLM-judge step whose sole job is to recover the unit from a free-form quote email.

→ Loop requires `rate_basis` on every priced `LineItem` (`per_unit`, `per_kg`, `per_cbm`, `per_container`, `per_shipment`, `all_in`).

### 5. Units arrive in whichever flavor the writer prefers

Emails contain lbs, cuft, inches, and "approx 1.2 m^3 ish." Pipelines build coercion layers (LLM-tolerant typed fields, regex-fallback parsers, kg/lb detectors).

→ Loop mandates canonical units in the freight extension: `KGM` for weight, `MTQ` for volume, `CMT` for length, ISO 4217 for currency. The format trades emitter convenience for receiver clarity.

### 6. Incoterms drift

Pipelines see `DDU` (deprecated since 2010), `DAT` (renamed to `DPU` in Incoterms 2020), `DTD` (not actually an Incoterm), and `DDP+DDU` (a contradiction in terms). Each shows up at least once a week.

→ Loop documents an explicit normalization table for deprecated codes and requires receivers to normalize on ingest.

### 7. Clarification is a first-class flow

A typical RFQ→quote cycle includes one or two clarification rounds: "what's the chargeable weight?", "is this DDP?", "do you have an MSDS?". When clarification is modeled as free-form replies, the receiving agent has to re-bind every answer to the field it concerns.

→ Loop defines `info_request` and `info_provided` messages with explicit question IDs and a `field_path` per question, so the answer can be merged back into the canonical record without LLM intervention.

### 8. Vertical specifics shouldn't fork the core

Freight needs MSDS fields, container taxonomies, customs filings. SaaS needs seat counts, metering, term length. Capex needs depreciation class. Trying to put all of these in one schema is how UBL ended up with thousands of fields.

→ Loop keeps the core message schemas tiny and pushes vertical specifics into namespaced `extensions.<vertical>`. Receivers preserve unknown extensions on relay so the network can grow without breaking older parsers.

### 9. Agents need to declare their own uncertainty

A receiver's confidence in its own extraction is a routing signal: low confidence should route to a human; high confidence should auto-quote. When the emitter is also an agent, *its* confidence in its own emission is just as useful — and it has information the receiver doesn't (which fields were inferred vs explicit, which questions it would have asked the human).

→ Loop includes an optional envelope-level `extraction_meta` block with `extraction_confidence`, `data_completeness`, and a `missing_fields` list pointing into the body. Receivers can use this to short-circuit their own classification or to surface "they're not sure either" to a human reviewer.

### 10. The format must survive a supplier that doesn't speak it

The receiving agent is not always an Loop speaker. Sometimes it's a human at a forwarding desk, sometimes it's a different procurement vendor's bot, sometimes it's a supplier with no automation at all.

→ Loop's email binding requires a human-readable rendering alongside the structured payload. The payload is a *bonus channel*, never a replacement channel. Suppliers who don't speak Loop lose nothing.

## What we didn't change

A few things in the original v0.1 draft survived the grounding exercise unchanged because they were already what the pipeline wanted:

- **JSON over XML.** No real agentic pipeline asked for XML.
- **Email as the reference transport.** Every real agent we looked at is operating over email today.
- **UUID-based `thread_id` / `message_id`.** Maps cleanly to Nylas / Microsoft Graph / Gmail thread identifiers.
- **Decimal strings for money.** Float precision is a real source of production bugs.
- **`extensions.<vertical>` namespacing.** This is the only architectural choice that lets the spec stay small while still being useful in a specific industry.

## Postscript: where this leaves us

Loop v0.1 is consciously a small spec. The bet is that the difference between "your agent re-extracts every RFQ from prose" and "your agent reads a typed payload directly" is large enough that even a small, opinionated standard delivers most of the value. Verticals can pile their specifics into extensions without forcing the core to grow. Receivers can adopt without forcing senders to. Senders can emit without forcing receivers to upgrade.

If that bet is right, Loop's reason to exist is the agent on the other side. Everything in this document is in service of that one constraint.
