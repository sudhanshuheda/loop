# Contributing to Loop

Loop is a v0.1 draft. The goal is to land at a stable v1.0 once the core has been exercised against real agentic procurement pipelines across at least three independent organizations. Until then, the spec is open to substantive change.

## What's most useful right now

In rough priority order:

1. **Real-world examples.** If you run an RFQ pipeline, send a sample message (with PII scrubbed) as an issue. We're especially interested in: services procurement, SaaS, capex, sea import flows, road freight, multimodal, anything outside the freight reference vertical.
2. **Schema bugs.** If a valid procurement scenario doesn't fit the schemas, that's a bug. File an issue with the example.
3. **Extension proposals.** Vertical-specific fields belong under `body.extensions.<vertical>`. New extensions land as a `docs/extensions/<vertical>.md` reference plus example messages.
4. **Binding implementations.** v0.1 ships the email binding. HTTPS webhook, MCP, and Slack bindings are open.
5. **SDKs.** Type-safe parsers / emitters in any language. JSON Schema 2020-12 codegen works for most.

## Development setup

```bash
make install      # creates .venv and installs jsonschema + referencing
make test         # runs both validators
```

`make validate` checks every example against its schema. `make validate-negative` checks that the schemas reject obviously wrong inputs. Both run on every PR via GitHub Actions.

## Changing the spec

Any change that affects the wire format is a v0.x bump unless it's strictly additive *and* unknown-field-tolerant. The bar:

- **Patch (0.1.x)**: documentation, examples, validator improvements.
- **Minor (0.x)**: additive schema changes. Unknown fields must remain ignorable; existing valid messages must remain valid.
- **Major (x.0)**: breaking changes. Coordinated; opt-in via transport-level signaling.

For any wire change:

1. Open an issue describing the change and a concrete message example.
2. Land the schema update and at least one passing example.
3. Update [`SPEC.md`](./SPEC.md) and [`CHANGELOG.md`](./CHANGELOG.md).
4. If it's a freight-extension change, update [`docs/extensions/freight.md`](./docs/extensions/freight.md).

## Style

- JSON: 2-space indent. Use a trailing newline. Order keys as they appear in the schema for readability.
- Markdown: Sentence case for headings. Reference files using relative links.
- Field names: `lower_snake_case`, English, LLM-friendly. No abbreviations unless universally recognized (UN, ISO, EU).
- Comments in code: only when the *why* is non-obvious. Code should be self-explanatory.

## Governance

Pre-1.0, the spec evolves through PRs reviewed by the current maintainer set listed in `MAINTAINERS.md` (when that file exists). At 1.0, Loop will move to a vendor-neutral home — likely a small working group or foundation. Until then, decisions favor speed of iteration over consensus.

If you'd like to be added as a co-maintainer, open an issue with the kind of contribution you'd like to lead.
