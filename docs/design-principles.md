# Design principles & rationale

Loop deliberately makes choices that look small but matter at scale. This doc records the "why" so future contributors don't reopen settled questions, and so detractors have an honest target.

## 1. Email-first, not API-first

**The principle.** Every Loop v0.1 message MUST be transportable over plain SMTP/IMAP without supplier onboarding.

**Why.** B2B procurement runs on email. Suppliers are a long tail: thousands of small forwarders, auditors, contract manufacturers, parts brokers. No standard wins by demanding every supplier register on a portal, get an API key, or accept webhooks. An open standard has to meet the long tail where it is.

**Trade-off.** Email is asynchronous, lossy in timing, and gives weak identity guarantees. We accept these costs; they're the same costs procurement absorbs today.

## 2. Mandatory human-readable fallback

**The principle.** Every Loop email MUST include a human-readable rendering alongside the structured payload.

**Why.** Adoption depends on the supplier-without-Loop case being just as good as today. The structured payload is a *bonus channel*, not a replacement channel. A supplier whose mail client doesn't surface attachments still reads a normal email.

**Trade-off.** Senders do duplicate work. We think it's worth it; the human rendering is what 90% of supplier UX looks like for the next several years.

## 3. JSON over XML

**Why.** Three reasons:
1. LLMs generate and consume JSON dramatically more reliably than XML. This is the single biggest practical lever.
2. Modern tooling (JSON Schema 2020-12, ajv, pydantic, zod, etc.) is universal and free.
3. JSON is denser and easier to embed in email body if attachments get stripped.

UBL and Peppol picked XML for reasons that made sense in 2004. They don't anymore.

## 4. LLM-friendly field names

**The principle.** Field names are lowercase, snake_case, English, and describe the thing (`quote_deadline`, not `QtDt` or `CBC:DueDate`).

**Why.** LLM emission and validation accuracy is sensitive to vocabulary. Names that read like product copy reduce hallucination and let small models (Haiku, GPT-4-mini class) emit Loop reliably.

**Trade-off.** Names are English-biased. Localized human-facing UI is the binding layer's problem, not the format's.

## 5. Tiny core + namespaced extensions

**The principle.** The core spec contains the union of fields every procurement message needs. Vertical specifics live under `body.extensions.<namespace>`.

**Why.** Universal-procurement standards historically choked on trying to model every industry. We avoid that by making the core boring and the extensions optional. Freight gets `extensions.freight`; SaaS gets `extensions.saas`. Vendors can ship their own extensions without spec changes.

**Conformance rule.** Agents MUST ignore unknown extensions and MUST preserve them on relay. That preserves forward compatibility without coordination.

## 6. Decimal strings, not floats

**The principle.** All monetary amounts, quantities, weights, and temperatures are strings of decimal digits.

**Why.** IEEE 754 floats silently corrupt money. A buyer's `2848.16` becoming `2848.1599999999999` because a JSON library rehydrated through `double` is a real production bug. Strings round-trip exactly.

## 7. Identity is the email address — for now

**The principle.** `issuer.email` is the v0.1 identity primitive. Transport-level identity (DKIM/SPF/DMARC) authenticates it.

**Why.** It's universal. It's what suppliers already authenticate with. It works today.

**What's deferred.** DIDs, verifiable credentials, signed envelopes (JWS), supplier directories. All planned. None blocking for v0.1.

## 8. No mandatory code lists where strings work

**The principle.** Where a code list exists and is universal (ISO 4217 currencies, ISO 3166 countries, UN/LOCODE ports), it's required. Where it's vertical or contested (procurement category codes, commodity codes), it's optional and free-form.

**Why.** Mandatory code lists are where universal standards go to die. Every adopter has a different reference data problem; insisting on one map drives them off.

## 9. Backwards-compatible by default

**The principle.** Minor versions only add. Unknown fields are preserved and ignored.

**Why.** Standards that break on minor version bumps don't get adopted at the long-tail end. We optimize for one-time integration and decade-long survival.

## 10. Optimize for the agent on the other end

**The principle.** When in doubt, choose the design that makes the *receiving* agent's job easier: structured over prose, explicit over inferred, IDs over heuristics, units always declared.

**Why.** This is the entire point. If Loop doesn't make the receiver's life dramatically simpler than scraping emails, it has no reason to exist.
