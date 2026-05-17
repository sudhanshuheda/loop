# Loop Extension: `freight` — v0.1

The `freight` extension carries the data a freight forwarder, customs broker, airline, shipping line, NVOCC, trucker, or rail operator needs to price and operate a shipment. It rides under `body.extensions.freight` on `rfq`, `quote`, and `po` messages.

The field surface is sized to cover what real agentic procurement pipelines extract today. Conformant freight implementations SHOULD populate as many of these fields as known. Conformant non-freight implementations MUST ignore this block and preserve it on relay.

## Shape

```json
{
  "mode":                    "air | sea | road | rail | multimodal",
  "offer_direction":         "import | export | cross_trade | internal_transfer",
  "sea_freight_type":        "FCL | LCL",
  "service_type":            "port_to_port | door_to_door | door_to_port | port_to_door",
  "service_level":           "standard | express | economy | other",

  "origin":                  { "...": "Address" },
  "destination":             { "...": "Address" },
  "pickup_address":          { "...": "Address, optional (required for EXW / door pickup)" },
  "delivery_address":        { "...": "Address, optional (required for DAP/DDP/DPU/CPT door delivery)" },
  "final_destination":       { "...": "Address, optional" },

  "incoterms":               "FCA | FOB | CIF | CIP | DAP | DDP | DPU | EXW | CPT | CFR | FAS",
  "incoterms_place":         "Bengaluru, IN",

  "ready_date":              "2026-05-22",
  "delivery_by":             "2026-05-30",
  "time_sensitive":          true,

  "commodity":               "Electronics, palletized",
  "hs_code":                 "8517.62.00",
  "hts_code":                "8517.62.0090",
  "cargo_type":              "general | hazardous | chilled | frozen | rolls | special_temperature",
  "commodity_attributes":    { "fragile": true, "battery_present": false },

  "pieces":                  2,
  "gross_weight":            { "value": "850",  "unit": "KGM" },
  "chargeable_weight":       { "value": "1100", "unit": "KGM" },
  "volume":                  { "value": "1.74", "unit": "MTQ" },
  "dimensional_factor":      6000,

  "containers": [
    {
      "type":        "40HC",
      "iso_type":    "45G1",
      "count":       1,
      "is_reefer":   false,
      "is_open_top": false,
      "is_flat_rack": false,
      "in_gauge":    true,
      "stackable":   true
    }
  ],

  "packages": [
    {
      "kind":        "pallet | carton | box | case | crate | bag | drum | skid | other",
      "count":       2,
      "weight_each": { "value": "425", "unit": "KGM" },
      "dimensions":  { "l": "120", "w": "100", "h": "145", "unit": "CMT" },
      "stackable":   false,
      "turnable":    true,
      "oversized":   false
    }
  ],

  "hazardous": {
    "is_hazardous":        true,
    "un_numbers":          ["UN3480"],
    "class_numbers":       ["9"],
    "packing_groups":      ["II"],
    "proper_shipping_name":"Lithium ion batteries",
    "msds_attachment_refs":["cid:msds-0"]
  },

  "temperature_controlled": {
    "required":     true,
    "min_celsius":  "2",
    "max_celsius":  "8",
    "ventilation":  "fresh air, 20 cbm/hr",
    "shelf_life":   "P30D"
  },

  "restricted_items": {
    "has_restricted":  false,
    "kind":            null,
    "details":         null
  },

  "declared_value":          { "amount": "18000.00", "currency": "USD" },
  "commercial_invoice_value":{ "amount": "18000.00", "currency": "USD" },
  "insurance":               { "required": true, "kind": "clause_a | clause_c", "covered_value": { "amount": "18000.00", "currency": "USD" } },

  "brokerage":               { "required": true, "side": "origin | destination | both" },
  "customs_filings":         { "expected": ["shipping_bill_in", "acas_us"] },

  "target_rate":             { "amount": "2700.00", "currency": "USD", "rate_basis": "per_shipment" },
  "carrier_preference":      ["Lufthansa Cargo", "Emirates SkyCargo"],
  "preferred_route":         "BLR-FRA direct preferred; BLR-DXB-FRA acceptable",

  "carrier":                 "Lufthansa Cargo",
  "carrier_routing":         "BLR-FRA direct (LH 757)",
  "vessel":                  "Maersk Stockholm V.243W",
  "transit_time":            { "min_days": 3, "max_days": 5, "notes": "subject to space" },

  "known_shipper":           "pax | cao | unknown",

  "consignee":               { "...": "Party" },
  "shipper":                 { "...": "Party" },
  "notify_party":            { "...": "Party" }
}
```

## Field reference

### Mode and direction

| Field              | Type    | Notes |
| ------------------ | ------- | ----- |
| `mode`             | enum    | Required if the extension is present. |
| `offer_direction`  | enum    | `import` / `export` / `cross_trade` (third-country to third-country) / `internal_transfer`. Important for forwarders running multi-direction desks. |
| `sea_freight_type` | enum    | `FCL` or `LCL`. Applies when `mode` is `sea`. |
| `service_type`     | enum    | The four common scopes: `port_to_port`, `door_to_door`, `door_to_port`, `port_to_door`. |
| `service_level`    | string  | Carrier-neutral level. Free-form fallback `other`. |

### Geography

| Field               | Type    | Notes |
| ------------------- | ------- | ----- |
| `origin`            | Address | Port / airport / origin city. UN/LOCODE `port_code` preferred for ports/airports. |
| `destination`       | Address | Same. |
| `pickup_address`    | Address | Required when `incoterms` is `EXW`, or when `service_type` includes door pickup. |
| `delivery_address`  | Address | Required when `incoterms` is `DAP` / `DDP` / `DPU` / `CPT` and door delivery is in scope. |
| `final_destination` | Address | When the goods continue past `delivery_address` (e.g. onward inland leg). |

### Commercial

| Field                      | Type    | Notes |
| -------------------------- | ------- | ----- |
| `incoterms`                | string  | Incoterms 2020. Normalize deprecated codes per SPEC §6. |
| `incoterms_place`          | string  | Required by Incoterms 2020 (e.g. `"FCA Bengaluru"` → place is `"Bengaluru"`). |
| `declared_value`           | Money   | Value declared for insurance / customs / liability cap. |
| `commercial_invoice_value` | Money   | Invoice value used for customs valuation. |
| `insurance`                | object  | `required`, `kind` (`clause_a` / `clause_c`), `covered_value`. |
| `target_rate`              | object  | Buyer-side rate expectation. Same shape as a `LineItem` price hint. |

### Schedule

| Field          | Type     | Notes |
| -------------- | -------- | ----- |
| `ready_date`   | date     | Cargo ready at origin. |
| `delivery_by`  | date     | Required arrival / delivery date. |
| `time_sensitive` | boolean| Soft urgency flag. |
| `transit_time` | object   | `{ min_days, max_days, notes }`. On quotes only. |

### Cargo characteristics

| Field                    | Type     | Notes |
| ------------------------ | -------- | ----- |
| `commodity`              | string   | Description in plain English. |
| `hs_code`                | string   | Harmonized System code. |
| `hts_code`               | string   | HTS code (US destination). |
| `cargo_type`             | enum     | `general` / `hazardous` / `chilled` / `frozen` / `rolls` / `special_temperature`. |
| `commodity_attributes`   | object   | Free-form structured attributes (`fragile`, `battery_present`, `food_contact`, `food_grade`, `religious_text`, `live_animal`, etc.). Buyer-side SOP signals belong here. |
| `pieces`                 | integer  | Total pieces. |
| `gross_weight`           | Quantity | Actual physical weight. |
| `chargeable_weight`      | Quantity | Volumetric or actual, whichever is higher. |
| `volume`                 | Quantity | Cubic measurement. |
| `dimensional_factor`     | integer  | Carrier-applied factor (6000 for air, 5000 for express courier). |

### Containers and packages

A shipment carries either `containers` (FCL / containerized rail) or `packages` (LCL / air / road palletized / parcel). Both MAY be present; pricing usually keys off one.

`containers[]`:

| Field          | Notes |
| -------------- | ----- |
| `type`         | Common short name (`20GP`, `40GP`, `40HC`, `45HC`, `20RF`, `40RF`, `20OT`, `40OT`, `20FR`, `40FR`, `20TK`, `RoRo`, …). |
| `iso_type`     | Optional ISO 6346 size/type code (`45G1`, `42R1`, …). |
| `count`        | Number of this container type. |
| `is_reefer`    | Refrigerated. |
| `is_open_top`  | Open-top container. |
| `is_flat_rack` | Flat-rack container. |
| `in_gauge`     | For OT/FR: dimensions within standard gauge. If `false`, populate `out_of_gauge_dimensions` in `commodity_attributes` or as a free-form note. |
| `stackable`    | Stackable in yard (only for OT/FR/loaded-special). |

`packages[]`:

| Field         | Notes |
| ------------- | ----- |
| `kind`        | `pallet` / `carton` / `box` / `case` / `crate` / `bag` / `drum` / `skid` / `other`. |
| `count`       | Number of this package type. |
| `weight_each` | Per-piece weight. |
| `dimensions`  | `{ l, w, h, unit }`. `unit` SHOULD be `CMT`. |
| `stackable`   | LCL stacking flag. |
| `turnable`    | Can the piece be turned (LCL oversized cargo). |
| `oversized`   | Considered oversized for LCL. |

### Hazardous

```json
{
  "is_hazardous":        true,
  "un_numbers":          ["UN3480"],
  "class_numbers":       ["9"],
  "packing_groups":      ["II"],
  "proper_shipping_name":"Lithium ion batteries",
  "msds_attachment_refs":["cid:msds-0"]
}
```

If `is_hazardous` is `false`, all other fields SHOULD be omitted. `un_numbers` / `class_numbers` are arrays to support consolidations.

### Temperature controlled

```json
{ "required": true, "min_celsius": "2", "max_celsius": "8", "ventilation": "fresh air, 20 cbm/hr", "shelf_life": "P30D" }
```

Temperatures use decimal strings. `shelf_life` is an ISO 8601 duration.

### Restricted items

```json
{ "has_restricted": false, "kind": null, "details": null }
```

Used to flag categories a carrier or forwarder may not be able to handle (live animals, religious texts to certain origins, hand-carry-only items, lighters / open flame on air). `kind` is free-form; common values include `live_animal`, `religious_text`, `lighter`, `hand_carry_only`. Senders MUST NOT use this block for normal hazmat — use `hazardous` instead.

### Brokerage / customs

```json
{ "brokerage": { "required": true, "side": "origin | destination | both" } }
```

Plus `customs_filings.expected`: an array of expected filings, drawn from:

- `shipping_bill_in` — Indian export Shipping Bill via ICEGATE
- `boe_in` — Indian Bill of Entry via ICEGATE
- `acas_us` — US Air Cargo Advance Screening
- `ams_us` — US ocean Automated Manifest System
- `isf_us` — US Importer Security Filing (10+2)
- `ens_eu` — EU Entry Summary Declaration (ICS2)
- `aes_us` — US Automated Export System

Verticals MAY extend this list. Receivers MUST ignore unknown values.

### Operational signals

| Field              | Notes |
| ------------------ | ----- |
| `carrier_preference` | Array of preferred carriers. |
| `preferred_route`    | Free-form routing hint. |
| `known_shipper`      | Air-specific: `pax` (passenger-eligible) / `cao` (cargo-aircraft-only) / `unknown`. |
| `carrier`            | Carrier the quote / PO is built against (quote / po only). |
| `carrier_routing`    | Routing summary (`"BLR-FRA direct (LH 757)"`). |
| `vessel`             | Sea: vessel + voyage (`"Maersk Stockholm V.243W"`). |

### Parties

| Field          | Notes |
| -------------- | ----- |
| `consignee`    | Receiving party at destination. Maps to BL/AWB consignee box. |
| `shipper`      | Origin shipper if distinct from envelope `issuer`. |
| `notify_party` | BL notify-party. |

## Quote-side fields

A `quote` `body.extensions.freight` block is permitted to add:

- `carrier`, `carrier_routing`, `vessel`, `transit_time`, `rate_basis_default`
- `validity_subject_to`: free-form text (e.g. `"subject to space availability at time of booking"`)
- `included_charges` / `excluded_charges`: arrays of free-form strings clarifying what the rate includes

These are conventional; the core `quote` body already carries the priced line items, charges, taxes, and total.

## Mode-specific guidance

- **Air**: Populate `chargeable_weight` and `dimensional_factor`. `carrier_routing` is informational; AWB modeling is deferred to v0.2.
- **Sea**: Use `containers[]` for FCL. For LCL, set `volume` and `gross_weight`; carriers compute revenue tons. Vessel format: `<vessel name> V.<voyage>`.
- **Road**: Use `packages[]`, `gross_weight`, `volume`. Trailer type goes in `service_level` or `commodity_attributes` until a richer road sub-extension lands.
- **Rail**: Treated like sea for containerized rail; like road for wagonload.
- **Multimodal**: Set `mode: "multimodal"` with top-level `origin` / `destination`. Per-leg routing is deferred to v0.2.

## Roadmap

Planned for `freight` v0.2+:

- AWB / BL / SI fields on `po` and dedicated `shipping_document` message.
- Per-leg routing for multimodal.
- Empty-container return location for sea import.
- Shipment event messages (`event_type`: booked, gated-in, loaded, departed, arrived, delivered, …).
- Customs filing references with submission ids.
- Detention & demurrage clock fields.
