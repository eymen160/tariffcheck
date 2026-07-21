# TariffCheck API Reference

All endpoints are served under `/api/`. The service is stateless — no database, no persistent disk. Deterministic endpoints (batch audit, landed cost, lookup, search, demos) work without an `ANTHROPIC_API_KEY`; only live AI analysis of real invoices requires one.

## Shared Error Shape

All new/changed error responses set the HTTP status correctly and return:

```json
{ "error": "machine_code", "message": "Human-readable sentence." }
```

- `error` is always a snake_case string code; `message` is a plain-English sentence with no developer instructions. Some endpoints add extra keys (noted per endpoint).
- Error bodies **never** contain `findings` or `total_savings` — a failed analysis can never look like a successful one.
- Clients **must** check `res.ok` before using any response body.

---

## POST /api/analyze

Audit a single invoice. Accepts any one of:

1. `multipart/form-data` with a `file` field (PDF or TXT)
2. `application/json` body: `{"text": "INVOICE...\n..."}`
3. Form field `text`
4. Demo request: form field or JSON key `demo_id` with value `"1"`–`"8"`. **Only an explicit `demo_id` returns mock data** — filename-based mock selection does not exist.

Demo responses are the built-in demo payloads passed through the same verifier, with `meta.demo: true` and the `verification` block attached.

### Success 200

```json
{
  "findings": [
    {
      "hts_code": "6109.90.10.90",
      "description": "Men's knit polo shirts, 100% polyester",
      "current_rate": 32.0,
      "section_301_rate": 0.0,
      "total_current_rate": 32.0,
      "suggested_code": "6109.10.00.12",
      "suggested_rate": 16.5,
      "total_suggested_rate": 16.5,
      "declared_value": 48000,
      "savings": 7440.0,
      "confidence": "high",
      "explanation": "Knit polo shirts of cotton are more specifically provided for under 6109.10...",
      "legal_basis": "GRI 1; Chapter 61 Note...",
      "verified": true,
      "verification_note": null,
      "model_claimed_savings": 8100.0
    }
  ],
  "total_savings": 7440.0,
  "fta_eligible": false,
  "fta_type": null,
  "fta_form_required": null,
  "country_of_origin": "Vietnam",
  "section_301_applies": false,
  "section_301_rate": 0.0,
  "protest_deadline_note": "Protests must be filed within 180 days of liquidation under 19 U.S.C. 1514.",
  "disclaimer": "Analysis assistance only; verify with a licensed customs broker before filing.",
  "protest_letter": "To: U.S. Customs and Border Protection...",
  "verification": {
    "source": "USITC HTS 2026 (29,755 codes)",
    "verified_count": 3,
    "total_count": 4,
    "suppressed_count": 1
  },
  "meta": {
    "demo": false,
    "model": "claude-haiku-4-5",
    "latency_ms": 14200
  }
}
```

Field semantics:

| Field | Notes |
|---|---|
| `findings[].savings` | **Always server-recomputed** when `verified: true` |
| `findings[].confidence` | Server-calibrated; unverified findings can never be `"high"` |
| `findings[].verified` | `true` iff both codes found in the USITC DB and savings recomputed |
| `findings[].verification_note` | String when `verified: false`, e.g. `"Suggested code not in USITC 2026 schedule"` or `"Rate not machine-parseable — manual review"`; otherwise `null` |
| `findings[].model_claimed_savings` | Present **only** if the model's math disagreed by more than $1 and was overwritten |
| `total_savings` | Sum of **verified** savings only, recomputed server-side |
| `protest_letter` | Always present; generated **after** verification, so it only contains verified numbers |
| `verification` | Always present on 200 |
| `verification.suppressed_count` | Findings dropped because the suggested code shares the current code's 8-digit subheading with an identical effective rate (same code reformatted / statistical-suffix shuffle — nothing to protest) |
| `meta` | Always present on 200; `demo` is `true` iff served from `demo_id` mock data |

### Errors

| Status | Body |
|---|---|
| 400 | `{"error":"text_too_short","message":"Invoice text too short. Please include product descriptions, HTS codes, values, and country of origin."}` |
| 422 | `{"error":"unreadable_file","message":"We couldn't read this file. Try a PDF with selectable text, or paste the invoice as text."}` |
| 429 | `{"error":"rate_limited","message":"Too many analyses from this address. Please wait a minute and retry."}` + header `Retry-After: <seconds>` |
| 502 | `{"error":"model_error","message":"The AI analysis failed. Please retry."}` |
| 503 | `{"error":"ai_unavailable","message":"Live AI analysis is not configured on this deployment. Try a sample scenario instead.","demo_available":true}` |
| 504 | `{"error":"model_timeout","message":"Analysis took too long. Try a shorter invoice or retry."}` |

---

## POST /api/analyze-batch

The broker feature: deterministic screen of 1–100 entry lines against the local USITC DB, curated misclassification patterns, and FTA/Section 301 recompute. **Zero Claude calls** — works with no API key, fast. Clients chunk larger sets into multiple requests.

### Request (`application/json`)

```json
{
  "rows": [
    {"row_id": 1, "hts_code": "9403.40.9060", "description": "Wooden kitchen cabinets", "declared_value": 12000, "origin": "China"},
    {"row_id": 2, "hts_code": "6109.90.1090", "description": "Men's cotton t-shirts", "declared_value": 8000, "origin": "Vietnam"}
  ]
}
```

| Field | Rules |
|---|---|
| `rows` | 1–100 rows per request |
| `row_id` | Any int or string; echoed back |
| `hts_code` | **Required**; digits/dots, 4–10 digits |
| `description` | Optional string |
| `declared_value` | Optional number; savings math skipped if absent |
| `origin` | Optional string |

### Success 200

```json
{
  "summary": {
    "rows": 2,
    "flagged": 1,
    "total_estimated_exposure": 3000.0,
    "source": "USITC HTS 2026 (29,755 codes)",
    "disclaimer": "Deterministic screen against the official schedule and curated misclassification patterns. Findings must be reviewed by a licensed customs broker or the importer of record before filing."
  },
  "results": [
    {
      "row_id": 1,
      "status": "flagged",
      "current_code": "9403.40.90.60",
      "current_code_found": true,
      "description": "Wooden kitchen cabinets",
      "declared_value": 12000,
      "origin": "China",
      "current_rate": 0.0,
      "section_301_rate": 25.0,
      "total_current_rate": 25.0,
      "issue": "possible_misclassification",
      "suggested_code": "9403.60.80.93",
      "suggested_rate": 0.0,
      "total_suggested_rate": 0.0,
      "estimated_savings": 3000.0,
      "confidence": "medium",
      "verified": true,
      "note": "Matches curated misclassification pattern: cabinets frequently misclassified under 9403.40."
    },
    {
      "row_id": 2, "status": "ok", "current_code": "6109.90.10.90", "current_code_found": true,
      "description": "Men's cotton t-shirts", "declared_value": 8000, "origin": "Vietnam",
      "current_rate": 32.0, "section_301_rate": 0.0, "total_current_rate": 32.0,
      "issue": null, "suggested_code": null, "suggested_rate": null, "total_suggested_rate": null,
      "estimated_savings": 0, "confidence": "high", "verified": true, "note": null
    }
  ]
}
```

Field semantics:

| Field | Notes |
|---|---|
| `results[].status` | `"flagged"` \| `"ok"` \| `"error"` |
| `results[].current_code` | Canonical dotted form; echo of input if not found |
| `results[].current_rate` | MFN %; `null` if unparseable |
| `results[].issue` | `"possible_misclassification"` \| `"missed_fta"` \| `"code_not_found"` \| `null` |
| `results[].suggested_code` | `null` when `issue` is `null` or `code_not_found` |
| `results[].estimated_savings` | `0` when `declared_value` absent |
| `results[].verified` | `true` for every non-error row (deterministic by construction) |

### Errors

| Status | Body |
|---|---|
| 400 | `{"error":"no_rows","message":"Provide 1-100 rows."}` |
| 400 | `{"error":"too_many_rows","message":"Maximum 100 rows per request — send in chunks."}` |
| 400 | `{"error":"invalid_row","message":"Row 3: hts_code is required."}` |

---

## GET /api/landed-cost

Deterministic landed-cost breakdown; CDN-cacheable.

```
GET /api/landed-cost?code=9403.40.9060&origin=China&value=50000&mode=ocean
```

| Param | Rules |
|---|---|
| `code` | Required |
| `origin` | Optional string (default `""`) |
| `value` | Required number > 0 (USD) |
| `mode` | `"ocean"` \| `"air"` (default `"ocean"`; HMF only applies to ocean) |

Response headers: `Cache-Control: public, s-maxage=86400, stale-while-revalidate=604800`

### Success 200

```json
{
  "found": true,
  "code": "9403.40.90.60",
  "matched_note": null,
  "description": "Kitchen cabinets, of wood...",
  "origin": "China",
  "value": 50000,
  "mode": "ocean",
  "breakdown": {
    "mfn_rate": 0.0,      "mfn_duty": 0.0,       "mfn_rate_raw": "Free",
    "section_301_rate": 25.0, "section_301_duty": 12500.0,
    "section_301_note": "Chapter-level estimate — confirm the exact Section 301 list for this code before relying on it.",
    "mpf_rate": 0.3464,   "mpf": 173.20,  "mpf_min": 33.58, "mpf_max": 651.50,
    "hmf_rate": 0.125,    "hmf": 62.50
  },
  "total_landed_duty": 12735.70,
  "effective_rate": 25.47,
  "fta": {
    "eligible": true, "name": "USMCA", "rate": 0.0, "form": "CBP Form 434",
    "duty_with_fta": 735.70, "savings": 12500.0
  },
  "disclaimer": "Estimate from the official USITC HTS 2026 schedule. Not customs advice; verify with a licensed broker."
}
```

Notes: `matched_note` is e.g. `"Matched at 6-digit level"` on prefix fallback. MPF min/max are 2026 figures (constants). `hmf` is `0.0` when `mode=air`. `effective_rate` is a % of `value`. `fta` is `null` when no applicable program exists for the origin.

### Errors

| Status | Body |
|---|---|
| 400 | `{"error":"invalid_params","message":"Provide code and a positive value."}` |
| 404 | `{"error":"code_not_found","message":"HTS code 9999.99 not found in the USITC schedule.","found":false}` |

---

## POST /api/leads

Stateless email capture. Validates the email with a simple regex, logs a structured JSON line (event `lead.captured` with email, source, context) to stdout, stores nothing, never echoes internal details.

### Request (`application/json`)

```json
{"email": "broker@firm.com", "source": "brokers_page", "context": "optional free text, max 500 chars"}
```

`source`: one of `"brokers_page"` | `"rate_alerts"` | `"pricing_page"` (unknown values accepted, logged as-is).

### Success 200

```json
{"ok": true, "message": "Thanks — we'll be in touch."}
```

### Errors

| Status | Body |
|---|---|
| 400 | `{"error":"invalid_email","message":"Provide a valid email address."}` |

---

# Unchanged Existing Endpoints

The following endpoints keep their existing shapes exactly.

## GET /api/health

### Success 200

```json
{
  "status": "ok",
  "version": "1.0.0",
  "service": "TariffCheck API",
  "hts_codes_loaded": 29755,
  "data_source": "USITC HTS 2026 (full schedule) + curated broker overlay",
  "claude_ready": true,
  "model": "claude-haiku-4-5",
  "fta_countries": 20
}
```

`claude_ready` reflects whether `ANTHROPIC_API_KEY` is configured; `model` is the value of `CLAUDE_MODEL` (default `claude-haiku-4-5`).

## GET /api/demo/&lt;1-8&gt;

Returns a pre-built demo analysis in the `/api/analyze` success shape (findings, `total_savings`, FTA fields, `protest_letter`). Unknown ids fall back to demo 1. `GET /api/demo` (no id) also returns demo 1.

```json
{
  "findings": [
    {
      "hts_code": "9403.90.8040",
      "description": "Executive office chairs, adjustable height, metal base, fabric upholstery",
      "current_rate": 5.3,
      "suggested_code": "9403.10.0000",
      "suggested_rate": 0.0,
      "declared_value": 64000,
      "savings": 3392,
      "explanation": "Metal-frame office chairs are specifically provided for under HTS 9403.10..."
    }
  ],
  "total_savings": 3392,
  "fta_eligible": true,
  "fta_type": "USMCA",
  "country_of_origin": "Mexico",
  "protest_letter": "To: U.S. Customs and Border Protection..."
}
```

Demo payloads requested through `POST /api/analyze` with `demo_id` additionally pass through the verifier and carry `verification` and `meta` (`meta.demo: true`).

## POST /api/hts-lookup

### Request (`application/json`)

```json
{"code": "9403.40.9060", "country_of_origin": "China"}
```

### Success 200

```json
{
  "found": true,
  "code": "9403.40.90.60",
  "matched_note": null,
  "description": "Kitchen cabinets, of wood...",
  "base_rate": 0.0,
  "base_rate_raw": "Free",
  "section_301_rate": 25.0,
  "total_effective_rate": 25.0,
  "fta_eligible": false,
  "fta_name": null,
  "fta_rate": null,
  "fta_form": null,
  "special_rates": {"A": "Free", "AU": "Free"},
  "units": ["No."],
  "chapter": "94",
  "notes": ""
}
```

### Errors

| Status | Body |
|---|---|
| 400 | `{"error": "Provide an HTS code"}` |
| 404 | `{"error": "HTS code 9999.99 not found in the USITC schedule", "found": false}` |

## GET /api/hts-search

```
GET /api/hts-search?q=wooden+furniture&limit=25
```

`q` must be at least 2 characters; `limit` defaults to 25, max 50. Matches by code prefix or description keywords.

### Success 200

```json
{
  "query": "wooden furniture",
  "count": 25,
  "results": [
    {
      "code": "9403.60.80.93",
      "description": "Other wooden furniture...",
      "general_rate": 0.0,
      "general_rate_raw": "Free",
      "special_rates": {"A": "Free"},
      "chapter": "94",
      "units": ["No."]
    }
  ]
}
```

### Errors

| Status | Body |
|---|---|
| 400 | `{"error": "Query must be at least 2 characters", "results": []}` |

---

## v3.1 additions (July 2026) — remedy routing, entry facts, ES-003 fields

All changes below are **additive and backward compatible**: existing requests keep working; new fields are optional.

### POST /api/analyze — optional entry facts

Accepts three optional fields (form fields with a file upload, or JSON keys with `text`):

| Field | Example | Effect |
|---|---|---|
| `entry_date` | `2025-09-01` | Enables the 19 U.S.C. 1520(d) one-year FTA window and the PSC 300-day window |
| `liquidation_status` | `liquidated` \| `not_liquidated` | Selects the classification vehicle: §1514 protest vs ACE PSC |
| `liquidation_date` | `2026-06-01` | Computes the real §1514 deadline (liquidation + 180 days) |

The response gains a `remedy_summary` block and the letter adapts to it (PSC request when unliquidated; expired-window advisory when the 180-day clock has run; §1514 protest with the computed deadline otherwise):

```json
"remedy_summary": {
  "liquidation_status": "liquidated",
  "classification_vehicle": "1514",
  "deadlines": {"psc": null, "protest_1514": "2026-11-28", "fta_1520d": "2026-09-01"},
  "notes": ["..."]
}
```

Per-finding `remedy` values: `"1514"` (reclassification, protestable), `"1520d"` (unclaimed FTA preference — carved out of the protest into a 1520(d) advisory block), or `null`.

### POST /api/analyze-batch — ACE ES-003 row fields

Each row additionally accepts: `entry_no`, `line_no`, `entry_date`, `liquidation_date`, `liquidation_status`, `duty_paid`, `spi_claimed`. Effects:

- `spi_claimed` present → the row is **never** flagged `missed_fta` (the program was claimed).
- `liquidation_date` → per-row `protest_by`, `protest_days_left`, `protest_window_open`.
- `liquidation_status` → per-row `remedy_vehicle`: `"psc"` (unliquidated) or `"1514"` (liquidated).
- `duty_paid` + `declared_value` → savings computed from actual dollars paid instead of schedule deltas.
- Origins may be ISO codes (`CN`, `MX`, `TR`) or names in any common spelling; the normalized value is echoed as `origin_normalized`.
- Rows whose rate is a specific/compound duty (e.g. ¢/kg) now return `confidence: "low"` with an explicit "NOT quantified" note instead of a silent `high`.

### Section 301 — line level

Section 301 rates are now applied at **line level** from the USITC "China Tariffs" table (10,391 covered 8-digit subheadings incl. all four-year-review increases in force July 2026; dataset: `backend/data/section301.json`, provenance in `section301_REPORT.md`). Codes whose coverage is limited to specific statistical lines are flagged as estimates in `verification_note` / landed-cost `s301_note`. Suspended List 4B codes correctly carry **no** additional duty.

### Auth (pilot)

Setting `TARIFFCHECK_API_KEYS` (comma-separated `key:FirmName` pairs) enables `X-API-Key` authentication: valid keys bypass the anonymous per-IP rate limit and usage is logged per firm. Setting `ALLOWED_ORIGINS` pins CORS. `LEADS_WEBHOOK_URL` forwards `/api/leads` submissions to a durable inbox; the leads endpoint also accepts `firm`, `entries_per_month`, `software` and a `website` honeypot field.

---

## v3.2 additions (July 2026) — white-label drafts, CORS/auth hardening

Additive and backward compatible.

### White-label protest drafts (Enterprise/pilot)

When a request to `POST /api/analyze` carries a valid `X-API-Key`, the firm name registered for that key (`TARIFFCHECK_API_KEYS` → `key:FirmName`) is used as the preparing office on the generated letter:

- The signature block reads "This document is a draft prepared for *FirmName* with TariffCheck's verification engine…" and adds a `Prepared by: FirmName` line.
- The response gains `"white_label": {"preparer_firm": "FirmName"}`.
- Anonymous (un-keyed) requests always get the plain TariffCheck draft — letterhead cannot be forged by an unauthenticated caller.
- The non-filer disclaimer ("TariffCheck does not file with CBP…") is a legal statement, not branding: it survives white-labeling. Firm names are sanitized to one printable line (≤80 chars).

### Hardening

- API-key comparison now uses `hmac.compare_digest` (constant-time).
- CORS: on Vercel **production**, an unset `ALLOWED_ORIGINS` no longer falls open to `*` — it pins to `https://tariffcheck-zeta.vercel.app`. Explicit `ALLOWED_ORIGINS` still wins; local/dev stays open.
