# Loop vs existing procurement standards

A short, honest comparison. Loop stands on the shoulders of every standard below; it doesn't claim to replace them everywhere — it claims to occupy the specific niche they don't fill.

## At a glance

| Standard    | Year | Format | Transport         | Primary niche                        |
| ----------- | ---- | ------ | ----------------- | ------------------------------------ |
| EDI X12     | 1979 | Flat   | VAN, AS2          | Large US enterprises, EDI VANs       |
| EDIFACT     | 1987 | Flat   | VAN, AS2          | Global trade, esp. EU/APAC           |
| cXML        | 1999 | XML    | HTTP POST         | Coupa/Ariba PunchOut, MRO catalogs   |
| UBL         | 2004 | XML    | HTTP / Peppol     | Government e-invoicing               |
| Peppol BIS  | 2008 | XML/UBL| Peppol network    | EU government procurement / e-invoicing |
| OAGIS BODs  | 2001 | XML    | Various           | ERP-to-ERP B2B                       |
| **Loop**    | 2026 | JSON   | Email (today)     | **Agent-to-agent procurement over email** |

## The case for each

- **EDI / EDIFACT** survives because banks, big retailers, and global trade infrastructure run on it. Don't replace it; it's not going anywhere. Loop is not for EDI VANs.
- **cXML** is Ariba's house format and the right answer when both parties run Coupa/Ariba. Loop is for everything outside that walled garden.
- **UBL / Peppol** is the right answer for government e-invoicing in the EU, Singapore, Australia, and a growing list of others. Loop is not e-invoicing; it's the *pre-invoice* lifecycle (RFQ, quote, PO).
- **OAGIS BODs** are good ERP integration grammar. Heavy. Not designed for an LLM to emit from a chat.

## What Loop does differently

1. **Agent emission is a first-class design constraint.** Every existing standard assumes the emitter is a deterministic system writing fields it knows. Loop assumes the emitter is an LLM, and optimizes naming, structure, and validation feedback accordingly.

2. **Email is the reference transport.** UBL/Peppol assume Peppol Access Points. cXML assumes HTTP POST endpoints. EDI assumes a VAN. Loop assumes Gmail.

3. **JSON, not XML.** Same reasons everyone else moved to JSON between 2010 and 2020. Procurement standards just didn't.

4. **Mandatory human-readable fallback.** No other procurement standard requires that the same message also be readable by a human in a normal email client. Loop does, because that's how it gets adopted by suppliers who don't speak it.

5. **Vertical extensions, not vertical forks.** Peppol BIS profiles fork the schema per country/industry. Loop keeps the core schema fixed and uses namespaced `extensions.*` to add vertical fields.

## When *not* to use Loop

- You're filing a regulated e-invoice in a Peppol jurisdiction. Use Peppol BIS Billing.
- You and your trading partner both run Ariba/Coupa and never leave it. Use cXML.
- You're moving high-volume EDI 850/855/856 between large enterprises with EDI infrastructure already in place. Stay on EDI.
- You need a signed, non-repudiable customs filing. Loop v0.1 doesn't sign; layer JWS later.

## Where Loop fits

The gap Loop targets is everything that today happens as a **free-form email between two organizations**:
- A buyer's procurement agent emails a long-tail supplier for a quote.
- A freight forwarder's agent emails an airline / shipping line / trucker for a rate.
- A finance team requests a quote from a service provider.
- Two AI agents — one on each side — try to negotiate without re-extracting the same data twice.

That's a large, growing, and currently unstandardized surface.
