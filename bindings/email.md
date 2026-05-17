# Loop Email Binding — v0.1

This document defines how to transport Loop messages over standard SMTP / IMAP email. It is the **reference binding** for Loop v0.1.

## Goals

1. **Zero supplier onboarding.** Suppliers who don't speak Loop still receive a normal, human-readable email.
2. **Lossless agent path.** Agents on both sides get the structured Loop JSON without scraping.
3. **Standards-compliant MIME.** No proprietary headers required for delivery; everything works through Gmail, Outlook, Exchange, Workspace, Postfix, etc.

## Message structure

Each Loop email is a `multipart/mixed` MIME message:

```
multipart/mixed
├── multipart/alternative
│   ├── text/plain    ← human-readable rendering (REQUIRED)
│   └── text/html     ← human-readable rendering (RECOMMENDED)
└── application/vnd.loop+json; version=0.1   ← the Loop payload (REQUIRED)
    Content-Disposition: attachment; filename="procurement.json"
```

### Required parts

| Part                                       | Required | Notes |
| ------------------------------------------ | -------- | ----- |
| `text/plain`                               | yes      | Human-readable summary of the message. Suppliers without Loop support read this. |
| `application/vnd.loop+json; version=0.1`   | yes      | The Loop JSON payload, attached as `procurement.json`. |

### Optional parts

| Part                | Notes |
| ------------------- | ----- |
| `text/html`         | Rich human-readable rendering. Encouraged. |
| Inline attachments  | Spec sheets, drawings, MSDS, etc. Referenced from Loop `attachments[].uri` using `cid:` URIs. |

## Headers

Senders SHOULD include the following `X-Loop-*` headers to enable cheap routing decisions before parsing the attachment:

| Header              | Value                                    | Required |
| ------------------- | ---------------------------------------- | -------- |
| `X-Loop-Version`    | `0.1`                                    | yes      |
| `X-Loop-Message-Type` | `rfq` / `quote` / `po` / `decline`     | yes      |
| `X-Loop-Message-Id` | the envelope `message_id` (UUID)         | yes      |
| `X-Loop-Thread-Id`  | the envelope `thread_id` (UUID)          | yes      |
| `X-Loop-In-Reply-To`| the envelope `in_reply_to`, if present   | no       |

The standard `Message-ID`, `In-Reply-To`, and `References` headers SHOULD also be set per RFC 5322 so that ordinary email clients thread the conversation correctly.

`Subject:` SHOULD mirror the envelope `subject` field.

## Optional in-body fenced block

Some mail clients (and some MTAs) strip attachments aggressively or filter unknown MIME types. As a defense in depth, senders MAY embed the Loop JSON in the `text/plain` part inside a fenced block:

```
…human-readable summary…

---LOOP-BEGIN v=0.1---
{ "loop_version": "0.1", "message_type": "rfq", ... }
---LOOP-END---

…optional human-readable closer…
```

The exact delimiters are:

- Open: `---LOOP-BEGIN v=<version>---`
- Close: `---LOOP-END---`

Each delimiter MUST occupy its own line. Recipients parsing the fenced block MUST:

1. Prefer the `application/vnd.loop+json` MIME attachment if both are present.
2. Verify byte-equality between the two if both are present; if they differ, treat the message as suspect and surface to a human.
3. Tolerate leading/trailing whitespace around the delimiters.

The fenced block is OPTIONAL. The attachment is the canonical carrier.

## Discovery

How does a buyer know whether a supplier speaks Loop? v0.1 takes the pragmatic approach:

1. **Just send.** Suppliers who don't speak Loop still read the human-readable email. Nothing breaks.
2. **Reciprocity signaling.** When a supplier sends back an Loop-formatted reply, the buyer knows the supplier is an Loop participant and can drop the human rendering on future messages in that thread (though keeping it is still RECOMMENDED).

Future versions will define an `X-Loop-Accept` capability header for explicit opt-in / opt-out.

## Inbound parsing rules

A receiving agent SHOULD process Loop email as follows:

1. **Detect.** If `X-Loop-Version` is present OR an attachment has media type `application/vnd.loop+json`, treat as Loop.
2. **Extract.** Prefer the attachment. Fall back to the fenced in-body block.
3. **Validate.** Against the schema for the declared `message_type`.
4. **Trust check.** Confirm the envelope `issuer.email` matches the DKIM-aligned `From:` (or is otherwise authenticated by your transport). Reject or quarantine mismatches.
5. **Thread.** Use the Loop `thread_id` as the canonical conversation identifier; cross-reference RFC 5322 `References:` for robustness.

## Worked example

```
From: Priya Shah <priya@acme.example>
To: Sales Desk <quotes@bluewing.example>
Subject: RFQ: Air freight BLR → FRA, 2 pallets electronics
Date: Sun, 17 May 2026 09:00:00 +0000
Message-ID: <9c2a8b8e-2c1f-4f3a-9d2b-7a1d2a3f4e5d@acme.example>
X-Loop-Version: 0.1
X-Loop-Message-Type: rfq
X-Loop-Message-Id: 9c2a8b8e-2c1f-4f3a-9d2b-7a1d2a3f4e5d
X-Loop-Thread-Id:  9c2a8b8e-2c1f-4f3a-9d2b-7a1d2a3f4e5d
MIME-Version: 1.0
Content-Type: multipart/mixed; boundary="loop-outer"

--loop-outer
Content-Type: multipart/alternative; boundary="loop-inner"

--loop-inner
Content-Type: text/plain; charset=utf-8

Hi BlueWing team,

Requesting a quote for air freight from Bengaluru (BLR) to Frankfurt (FRA):

  • Mode:    Air, standard
  • Cargo:   2 pallets electronics, non-hazardous
  • Weight:  850 kg gross / 1100 kg chargeable
  • Volume:  1.74 m³
  • Ready:   2026-05-22
  • Incoterms: FCA BLR
  • Insurance value: USD 18,000

Quote deadline: 2026-05-19 12:00 UTC. Validity expected: 14 days.

A structured Loop payload is attached as procurement.json.

Thanks,
Priya

--loop-inner
Content-Type: text/html; charset=utf-8

<html>…rich rendering…</html>

--loop-inner--

--loop-outer
Content-Type: application/vnd.loop+json; version=0.1
Content-Disposition: attachment; filename="procurement.json"

{ "loop_version": "0.1", "message_type": "rfq", ... }

--loop-outer--
```

## Security and abuse considerations

- **Spoofing.** Loop gives an agent more reasons to act automatically on an email. Always confirm that `issuer.email` is DKIM-aligned with `From:`. Reject otherwise.
- **Payload size.** Cap `procurement.json` at a reasonable size (e.g. 1 MiB) and reject oversized payloads. Real procurement messages are small.
- **Recursion / depth.** Cap JSON nesting depth (e.g. 32) to prevent parser denial-of-service.
- **Attachment fanout.** Do not auto-fetch external `https:` attachment URIs without policy controls.
