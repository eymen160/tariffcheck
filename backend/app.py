from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from pathlib import Path
import anthropic
import PyPDF2
import pdfplumber
import hmac
import json
import logging
import re
import io
import os
import time
from dotenv import load_dotenv
from hts_database import (
    lookup_hts,
    check_fta,
    fta_rate_for_code,
    search_hts,
    HTS_RATES,
    FTA_COUNTRIES,
    get_misclassification_hint,
    get_misclassification_hints,
    get_section_301_rate,
    get_section_301,
)
from verifier import verify_findings, VERIFICATION_SOURCE
from remedy import build_remedy_summary
from batch_audit import run_batch_audit, BatchValidationError
from entry7501 import parse_7501, Form7501Error
from hs2028 import check_code as hs2028_check_code, check_codes as hs2028_check_codes
import db

load_dotenv()

VERSION = "3.5.0"
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-haiku-4-5")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
log = logging.getLogger("tariffcheck")

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB upload cap

# CORS: pin to product origins via ALLOWED_ORIGINS (comma-separated). On
# Vercel *production* an unset var no longer falls open to "*" — it pins to
# the known product origin, because origins="*" lets any third-party site
# drive the Claude-spending /api/analyze endpoint from its visitors'
# browsers. Local/dev (no VERCEL_ENV) keeps the open default.
PROD_ORIGIN = "https://tariffcheck-zeta.vercel.app"


def _resolve_origins(allowed_origins_env, vercel_env):
    explicit = [o.strip() for o in (allowed_origins_env or "").split(",") if o.strip()]
    if explicit:
        return explicit
    if (vercel_env or "").strip().lower() == "production":
        return [PROD_ORIGIN]
    return "*"


_origins = _resolve_origins(os.getenv("ALLOWED_ORIGINS", ""),
                            os.getenv("VERCEL_ENV", ""))
CORS(app, origins=_origins)
if _origins == "*":
    logging.getLogger("tariffcheck").warning(
        "ALLOWED_ORIGINS not set — CORS is wide open; set it in production.")

def api_error(status, code, message, headers=None, **extra):
    """Shared error shape: {"error": <machine_code>, "message": <human sentence>}.
    Error bodies never contain findings/total_savings — a failed analysis must
    be unmistakably a failure, not a fake-success $0 result."""
    body = {"error": code, "message": message}
    body.update(extra)
    response = jsonify(body)
    response.status_code = status
    for key, value in (headers or {}).items():
        response.headers[key] = value
    return response


class AIUnavailableError(Exception):
    """No usable ANTHROPIC_API_KEY on this deployment."""


class ModelResponseError(Exception):
    """The model refused or returned an unusable payload."""


# ── Rate limiting: in-memory per-IP sliding window ──────────────────────────
# Module-level dict — per-instance state only, which is exactly what a
# stateless Vercel deployment allows. demo_id requests are exempt.
RATE_LIMIT_MAX = 10          # requests
RATE_LIMIT_WINDOW = 300      # seconds
_RATE_BUCKETS = {}           # ip -> [timestamps]


def _client_ip():
    forwarded = request.headers.get("X-Forwarded-For", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.remote_addr or "unknown"


def api_key_firm():
    """Pilot-grade API-key auth: TARIFFCHECK_API_KEYS holds comma-separated
    "key:FirmName" pairs. A valid X-API-Key identifies the firm and bypasses
    the anonymous per-IP rate limit (their usage is logged per firm instead).
    No env var → feature off, everything stays anonymous+rate-limited."""
    supplied = (request.headers.get("X-API-Key") or "").strip()
    if not supplied:
        return None
    raw = os.getenv("TARIFFCHECK_API_KEYS", "").strip()
    for pair in raw.split(",") if raw else ():
        key, _, firm = pair.strip().partition(":")
        if key and hmac.compare_digest(key, supplied):
            return firm or "unnamed"
    # DB-issued keys (stored hashed) — a no-op unless DATABASE_URL is set.
    return db.lookup_api_key(supplied)


def check_rate_limit():
    """Returns None when allowed, or seconds to wait when over the limit."""
    now = time.time()
    ip = _client_ip()
    bucket = [t for t in _RATE_BUCKETS.get(ip, []) if now - t < RATE_LIMIT_WINDOW]
    if len(bucket) >= RATE_LIMIT_MAX:
        _RATE_BUCKETS[ip] = bucket
        return max(1, int(RATE_LIMIT_WINDOW - (now - bucket[0])) + 1)
    bucket.append(now)
    _RATE_BUCKETS[ip] = bucket
    # Opportunistic cleanup so the dict can't grow unbounded per instance
    if len(_RATE_BUCKETS) > 10000:
        _RATE_BUCKETS.clear()
        _RATE_BUCKETS[ip] = bucket
    return None

SYSTEM_PROMPT = """You are a licensed US customs broker and trade compliance specialist with 20 years of experience. You specialize in HTS classification for furniture/cabinets, natural stone, apparel, and consumer goods.

EXPERTISE AREAS:
- Chapter 94 furniture: kitchen cabinets (9403.40), closets (9403.89), bedroom furniture (9403.50), parts (9403.90)
- Chapter 68 stone: polished marble countertops (6802.91) vs raw slabs (6802.21), granite (6802.93), travertine
- Chapter 61/62 apparel: chief weight cotton rule (6109.10 vs 6109.90), sports footwear (6404.11 vs 6404.19)
- Chapter 73 tumblers: stainless steel (7323.93 at 2%) vs vacuum flasks (9617 at 7.2%)
- Section 301 China tariff stacking: List 3 (25% for Ch.94 furniture, hardware), List 4A (7.5% for apparel)
- FTA preferences: USMCA (Canada/Mexico), KORUS (South Korea), CTPA (Colombia)
- Vietnam: NO Section 301, NO FTA — only base MFN rate
- China: NO FTA — Section 301 stacks on top of base rate

YOUR TASK: Analyze this commercial invoice and find every duty savings opportunity.

CHECK IN THIS ORDER:
1. HTS MISCLASSIFICATION: Is the declared code the most specific correct subheading?
   - For wooden furniture: is it kitchen (9403.40) vs bedroom (9403.50) vs other (9403.60/9403.89)?
   - For stone: is it raw/cut (6802.21) or polished/finished (6802.91)? Polished is different rate.
   - For apparel: what is the chief weight? Cotton >50% → 6109.10 (16.5%) not 6109.90 (32%)
   - For tumblers: single-wall or double-wall? True vacuum → consider 9617, but most stainless tumblers → 7323.93
2. FTA NOT CLAIMED: Canada/Mexico → USMCA. South Korea → KORUS. Colombia → CTPA.
3. SECTION 301 ACCURACY: For China goods, is the correct Section 301 layer applied?
   - Chapter 94 furniture from China: base rate + 25% Section 301
   - Chapter 61/62 apparel from China: base rate + 7.5% Section 301
   - Natural stone (Ch.68) from China: NO Section 301
   - Vietnam: NO Section 301 at all
4. OVERPAYMENT FROM WRONG SECTION 301: Did importer apply Section 301 to non-China goods?
5. PARTS vs ASSEMBLED: Cabinet parts (9403.90) vs assembled cabinets (9403.40) — different codes

IMPORTANT RULES:
- NEVER invent savings that do not exist. Accuracy above all.
- If current classification is correct, say so clearly with explanation.
- RECLASSIFICATION BAR: propose a different code ONLY when you can cite the
  specific GRI rule, section/chapter note, or CBP ruling the declared code
  violates. "Another code could also fit" is not a finding; "the declared
  code is wrong because <specific rule>" is. When the declared code is
  plausible and defensible, leave it alone.
- If an invoice line cites a CBP ruling number for its classification,
  treat that ruling as controlling for that product — do not contradict it.
- NEVER present the declared code itself as a misclassification —
  reformatted, truncated, or with a different statistical suffix (same
  first 8 digits) is still the same classification, not a finding.
- Unclaimed FTA preference or wrongly applied Section 301 on a CORRECTLY
  classified line IS a finding: keep suggested_code equal to the declared
  code and put the program savings in the numbers.
- For Vietnam-origin furniture: rate is just the base MFN rate (usually 0% for Ch.94). No Section 301.
- For China furniture: base rate (usually 0%) + 25% Section 301 = 25% total effective rate.
- Always note: 180-day protest deadline from liquidation per 19 U.S.C. §1514(a)(2)
- Use confidence: "high" (clear ruling/rule), "medium" (reasonable interpretation), "low" (ambiguous)

Return ONLY valid JSON, no markdown fences, no preamble:
{
  "findings": [
    {
      "hts_code": "9403.60.8040",
      "description": "exact product description from invoice",
      "current_rate": 0.0,
      "section_301_rate": 25.0,
      "total_current_rate": 25.0,
      "suggested_code": "9403.40.9060",
      "suggested_rate": 0.0,
      "section_301_applies_suggested": true,
      "total_suggested_rate": 25.0,
      "declared_value": 48000,
      "savings": 0,
      "classification_risk": true,
      "confidence": "high",
      "explanation": "Plain English explanation. Include what the correct rule is and why.",
      "legal_basis": "GRI Rule 1, Chapter 94 Note, or CBP Ruling [number if known]",
      "action_required": "File protest" or "Correct future entries" or "No action needed"
    }
  ],
  "total_savings": 0,
  "fta_eligible": false,
  "fta_type": null,
  "fta_form_required": null,
  "country_of_origin": "Vietnam",
  "section_301_applies": false,
  "section_301_rate": 0.0,
  "protest_deadline_note": "180 days from liquidation date per 19 U.S.C. §1514(a)(2)",
  "cape_eligible": false,
  "cape_note": "IEEPA refunds do not apply here. Savings from HTS misclassification require CBP protest.",
  "disclaimer": "TariffCheck analysis is for informational purposes only. Consult a licensed customs broker before filing."
}"""


def extract_text_from_pdf(file_bytes):
    # Try pdfplumber first — preserves table layout and spacing much better than PyPDF2
    try:
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            pages = []
            for page in pdf.pages:
                # Extract tables first to capture HTS codes in table cells
                tables = page.extract_tables()
                if tables:
                    for table in tables:
                        for row in table:
                            pages.append("  |  ".join(str(cell or "").strip() for cell in row))
                # Also extract raw text for non-table content
                text = page.extract_text(x_tolerance=3, y_tolerance=3)
                if text:
                    pages.append(text)
            result = "\n".join(pages).strip()
            if result:
                # Normalize HTS codes that got split by whitespace during extraction
                # e.g. "9403.10. 0000" → "9403.10.0000", "9403 .10.0000" → "9403.10.0000"
                result = re.sub(r'(\d{4})\s*\.\s*(\d{2})\s*\.\s*(\d{4})', r'\1.\2.\3', result)
                result = re.sub(r'(\d{4})\s*\.\s*(\d{2})\b', r'\1.\2', result)
                return result
    except Exception as e:
        log.warning(f"pdfplumber error: {e}")

    # Fallback to PyPDF2
    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
        text = ""
        for page in pdf_reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"
        result = text.strip()
        result = re.sub(r'(\d{4})\s*\.\s*(\d{2})\s*\.\s*(\d{4})', r'\1.\2.\3', result)
        result = re.sub(r'(\d{4})\s*\.\s*(\d{2})\b', r'\1.\2', result)
        return result
    except Exception as e:
        log.error(f"PDF extraction error: {e}")
        return ""


# JSON Schema enforced via structured outputs — guarantees parseable analysis
ANALYSIS_SCHEMA = {
    "type": "object",
    "properties": {
        "findings": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "hts_code": {"type": "string"},
                    "description": {"type": "string"},
                    "current_rate": {"type": "number"},
                    "section_301_rate": {"type": "number"},
                    "total_current_rate": {"type": "number"},
                    "suggested_code": {"type": "string"},
                    "suggested_rate": {"type": "number"},
                    "section_301_applies_suggested": {"type": "boolean"},
                    "total_suggested_rate": {"type": "number"},
                    "declared_value": {"type": "number"},
                    "savings": {"type": "number"},
                    "classification_risk": {"type": "boolean"},
                    "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
                    "explanation": {"type": "string"},
                    "legal_basis": {"type": "string"},
                    "action_required": {"type": "string"},
                },
                "required": [
                    "hts_code", "description", "current_rate", "suggested_code",
                    "suggested_rate", "declared_value", "savings", "confidence",
                    "explanation",
                ],
                "additionalProperties": False,
            },
        },
        "total_savings": {"type": "number"},
        "fta_eligible": {"type": "boolean"},
        "fta_type": {"type": ["string", "null"]},
        "fta_form_required": {"type": ["string", "null"]},
        "country_of_origin": {"type": ["string", "null"]},
        "section_301_applies": {"type": "boolean"},
        "section_301_rate": {"type": "number"},
        "protest_deadline_note": {"type": "string"},
        "disclaimer": {"type": "string"},
    },
    "required": ["findings", "total_savings", "fta_eligible", "country_of_origin"],
    "additionalProperties": False,
}

# Longest patterns first — regex alternation is ordered and would otherwise
# match "9403.60" out of "9403.60.8040" and stop.
HTS_CODE_RE = re.compile(
    r"\b(\d{4}\.\d{2}\.\d{2}\.\d{2}"   # 9403.60.80.40 (USITC dotting)
    r"|\d{4}\.\d{2}\.\d{4}"            # 9403.60.8040  (CBP entry dotting)
    r"|\d{4}\.\d{2}\.\d{2}"            # 9403.60.80
    r"|\d{4}\.\d{2}"                   # 9403.60
    r"|\d{8,10})\b"                    # 9403608040
)


def build_grounding_block(invoice_text):
    """Extract HTS codes from the invoice and look each one up in the official
    USITC schedule. The verified rates are injected into the prompt so the
    model reasons from real tariff data instead of memory."""
    seen = set()
    lines = []
    for match in HTS_CODE_RE.findall(invoice_text):
        digits = re.sub(r"\D", "", match)
        if len(digits) < 6 or digits in seen:
            continue
        seen.add(digits)
        rec = lookup_hts(digits)
        if not rec:
            lines.append(f"- {match}: NOT FOUND in the 2026 USITC schedule — likely invalid or retired code.")
            continue
        rate = rec.get("general_raw") or (f"{rec.get('general_rate')}%" if rec.get("general_rate") is not None else "unknown")
        special = rec.get("special_rates") or {}
        fta_progs = ", ".join(sorted(special)) if special else "none"
        lines.append(
            f"- {rec['code']}: \"{rec.get('description', '')[:160]}\" — general rate: {rate}; "
            f"FTA programs with special rate: {fta_progs}"
        )
        if len(seen) >= 25:
            break
    if not lines:
        return ""
    return (
        "\n\nVERIFIED USITC 2026 TARIFF DATA for the HTS codes found on this invoice "
        "(authoritative — use these rates, not memory):\n" + "\n".join(lines)
    )


def analyze_with_claude(invoice_text):
    """Run the Claude analysis. Raises typed exceptions so analyze() can map
    honest HTTP statuses instead of collapsing every failure to a fake demo
    response:
      AIUnavailableError          → 503 ai_unavailable
      anthropic.RateLimitError    → 429 rate_limited (Retry-After passthrough)
      anthropic.APITimeoutError   → 504 model_timeout
      anthropic.APIStatusError    → 502 model_error
      ModelResponseError          → 502 model_error
    """
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key or api_key in ("dummy", "dummy_key_for_demo", "your_key_here"):
        raise AIUnavailableError("No valid ANTHROPIC_API_KEY configured")

    # timeout=45s / max_retries=1 keeps worst-case latency inside Vercel's
    # 60s function window instead of the SDK default (10 min, 2 retries).
    client = anthropic.Anthropic(api_key=api_key, timeout=45.0, max_retries=1)

    grounding = build_grounding_block(invoice_text)

    started = time.time()
    # Structured outputs guarantee schema-valid JSON — no manual brace hunting.
    # System prompt is static → cache it; per-invoice content goes in the user turn.
    message = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=4000,
        system=[{
            "type": "text",
            "text": SYSTEM_PROMPT,
            "cache_control": {"type": "ephemeral"},
        }],
        output_config={"format": {"type": "json_schema", "schema": ANALYSIS_SCHEMA}},
        messages=[
            {
                "role": "user",
                "content": (
                    "Analyze this customs invoice and find HTS misclassification savings:\n\n"
                    f"{invoice_text[:8000]}{grounding}"
                ),
            }
        ],
    )
    latency_ms = int((time.time() - started) * 1000)

    usage = getattr(message, "usage", None)
    if usage is not None:
        log.info(json.dumps({
            "event": "analyze.usage",
            "model": CLAUDE_MODEL,
            "input_tokens": getattr(usage, "input_tokens", None),
            "output_tokens": getattr(usage, "output_tokens", None),
            "cache_read_input_tokens": getattr(usage, "cache_read_input_tokens", None),
            "cache_creation_input_tokens": getattr(usage, "cache_creation_input_tokens", None),
            "latency_ms": latency_ms,
        }))

    if message.stop_reason == "refusal":
        log.warning("Claude declined the request (stop_reason=refusal)")
        raise ModelResponseError("Model declined the request")
    try:
        return json.loads(message.content[0].text)
    except (ValueError, IndexError, AttributeError) as e:
        raise ModelResponseError(f"Unparseable model output: {e}") from e


def _sanitize_firm_name(value):
    """One printable line, bounded length — letterhead input can't break the
    letter structure or smuggle control characters."""
    cleaned = re.sub(r"[\x00-\x1f\x7f]+", " ", str(value or ""))
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned[:80] or None


def generate_protest_letter(findings, total_savings, fta_type=None, remedy_summary=None,
                            preparer_firm=None):
    # Only verified findings may reach the legal artifact — every number below
    # was recomputed server-side against the USITC schedule by verify_findings.
    # preparer_firm (Enterprise/pilot white-label): the API-keyed firm's name
    # appears as the preparing office. The non-filer disclaimer is a legal
    # statement, not branding — it survives white-labeling.
    preparer_firm = _sanitize_firm_name(preparer_firm)
    # Remedy routing: unclaimed FTA preferences are NOT protestable under
    # §1514 (CBP rejects them; the exclusive vehicle is 19 U.S.C. 1520(d)),
    # so they are carved out of the protest into a separate advisory block.
    # Entry-level vehicle selection (remedy_summary) then decides whether the
    # classification corrections travel as a §1514 protest (liquidated), an
    # ACE PSC (not yet liquidated), or an expired-window advisory.
    verified = [
        f for f in (findings or [])
        if f.get('verified') and f.get('savings', 0) > 0
    ]
    protestable = [f for f in verified if f.get('remedy', '1514') == '1514']
    fta_claims = [f for f in verified if f.get('remedy') == '1520d']

    protest_total = round(sum(f.get('savings', 0) for f in protestable), 2)
    fta_total = round(sum(f.get('savings', 0) for f in fta_claims), 2)

    vehicle = (remedy_summary or {}).get('classification_vehicle') or '1514'
    deadlines = (remedy_summary or {}).get('deadlines') or {}

    fta_deadline_line = ""
    if deadlines.get('fta_1520d'):
        fta_deadline_line = f"\n1520(d) filing deadline for this entry: {deadlines['fta_1520d']}."

    fta_text = ""
    if fta_claims:
        fta_items = "\n".join(
            f"- HTS {f.get('suggested_code')}: unclaimed preference worth ${f.get('savings', 0):,.2f}"
            for f in fta_claims
        )
        fta_text = f"""UNCLAIMED FTA PREFERENCES — NOT PART OF THIS PROTEST:
The following recoverable amounts arise from free-trade-agreement preferences
that were not claimed at entry. These are not protestable under 19 U.S.C.
§1514; the exclusive vehicle is a post-importation claim under 19 U.S.C.
1520(d), filed within ONE YEAR of the date of importation with a valid
certification of origin. Ask your licensed customs broker to file the 1520(d)
claim separately.{fta_deadline_line}
{fta_items}
Estimated FTA recovery: ${fta_total:,.2f}"""

    if preparer_firm:
        prepared_clause = (
            f"This document is a draft prepared for {preparer_firm} with "
            "TariffCheck's verification engine and checked against the")
        preparer_block = f"Prepared by: {preparer_firm}\n\n"
    else:
        prepared_clause = (
            "This document is a draft prepared with TariffCheck and verified "
            "against the")
        preparer_block = ""

    signature = f"""{prepared_clause}
official USITC HTS 2026 schedule. It must be reviewed, completed (entry
numbers, liquidation dates, protestant details), and filed by the importer of
record or a licensed customs broker. TariffCheck does not file with CBP and
does not act as the importer's representative.

{preparer_block}Submitted by (importer of record / licensed customs broker):

Name: ______________________________  IOR / License No.: ____________________

Signature: _________________________  Date: _________________________________"""

    if not protestable or protest_total == 0:
        if fta_claims:
            return f"""No §1514 protest basis identified — the classifications reviewed appear correct.

{fta_text}

{signature}"""
        return "No protest needed — current classification appears correct."

    items = "\n".join([
        f"- HTS {f.get('hts_code')} → {f.get('suggested_code')} (save ${f.get('savings', 0):,.0f})"
        for f in protestable
    ])

    if vehicle == 'psc':
        psc_line = ""
        if deadlines.get('psc'):
            psc_line = f" PSC filing deadline for this entry (300 days from entry): {deadlines['psc']}."
        body = f"""To: U.S. Customs and Border Protection
(via ACE Post Summary Correction)

Re: Request for Post Summary Correction — Tariff Classification

This entry has NOT yet liquidated, so the correct vehicle for these classification corrections is an ACE Post Summary Correction (19 U.S.C. 1501), filed within 300 days of the entry date and at least 15 days before the scheduled liquidation date.{psc_line} A protest under 19 U.S.C. §1514 is not yet available and would be premature.

The following corrections are requested:
{items}

The total duty reduction from the corrected classifications amounts to ${protest_total:,.2f}. Corrected rates were verified against the official USITC HTS 2026 schedule."""
    elif vehicle == '1514_expired':
        expired_line = ""
        if deadlines.get('protest_1514'):
            expired_line = f" The 180-day window from the reported liquidation date appears to have closed on {deadlines['protest_1514']}."
        body = f"""ADVISORY — PROTEST WINDOW APPEARS CLOSED

The classification findings below are verified against the USITC HTS 2026 schedule, but based on the liquidation information provided, the 19 U.S.C. §1514 protest deadline for this entry appears to have passed.{expired_line} Confirm the actual liquidation date on the ACE courtesy notice before abandoning the claim — and review current entries so the same overpayment stops recurring.

Findings (for review, not for filing):
{items}

Verified overpayment identified: ${protest_total:,.2f}."""
    else:
        deadline_line = ""
        if deadlines.get('protest_1514'):
            deadline_line = f"\n\nProtest filing deadline (180 days from the reported liquidation date): {deadlines['protest_1514']}."
        elif vehicle == 'unknown':
            deadline_line = (
                "\n\nIMPORTANT: liquidation status was not provided. Confirm this "
                "entry has liquidated before filing — a §1514 protest filed "
                "before liquidation is invalid; if the entry is still open, "
                "file these corrections as an ACE Post Summary Correction instead."
            )
        body = f"""To: U.S. Customs and Border Protection
Port Director

Re: Protest of Tariff Classification

Dear Port Director,

Pursuant to 19 U.S.C. §1514(a)(2), the importer hereby protests the tariff classification of imported merchandise and requests reliquidation of the affected entries.

The following misclassifications were identified:
{items}

The total overpayment of duties subject to this protest amounts to ${protest_total:,.2f}. We respectfully request that CBP reliquidate these entries under the correct HTS classifications and refund the excess duties paid within the statutory timeframe.{deadline_line}"""

    if fta_text:
        body += f"\n\n{fta_text}"

    return f"{body}\n\n{signature}"


MIN_INVOICE_CHARS = 20


def _requested_demo_id():
    """Mock data is served ONLY for an explicit demo_id (form field or JSON
    key) — filename-based mock selection is gone for good."""
    demo_id = request.form.get('demo_id')
    if demo_id is None and request.is_json:
        data = request.get_json(silent=True) or {}
        demo_id = data.get('demo_id')
    return str(demo_id) if demo_id is not None else None


@app.route('/analyze', methods=['POST'])
@app.route('/api/analyze', methods=['POST'])
def analyze():
    started = time.time()
    try:
        # Explicit demo request → mock data (verified at import time),
        # exempt from rate limiting because it costs nothing.
        demo_id = _requested_demo_id()
        if demo_id is not None:
            demo = MOCK_DEMOS.get(demo_id, MOCK_DEMOS["1"])
            payload = {**demo, "meta": {
                "demo": True,
                "model": CLAUDE_MODEL,
                "latency_ms": int((time.time() - started) * 1000),
            }}
            return jsonify(payload)

        firm = api_key_firm()
        if firm is None:
            wait = check_rate_limit()
            if wait is not None:
                return api_error(
                    429, "rate_limited",
                    "Too many analyses from this address. Please wait a minute and retry.",
                    headers={"Retry-After": str(wait)},
                )
        else:
            log.info(json.dumps({"event": "api_key.analyze", "firm": firm}))

        invoice_text = ""
        if request.files and 'file' in request.files:
            file = request.files['file']
            file_bytes = file.read()
            if file.filename and file.filename.lower().endswith('.pdf'):
                if not file_bytes.startswith(b'%PDF-'):
                    return api_error(
                        422, "unreadable_file",
                        "We couldn't read this file. Try a PDF with selectable text, "
                        "or paste the invoice as text.",
                    )
                invoice_text = extract_text_from_pdf(file_bytes)
                if len(invoice_text.strip()) < MIN_INVOICE_CHARS:
                    return api_error(
                        422, "unreadable_file",
                        "We couldn't read this file. Try a PDF with selectable text, "
                        "or paste the invoice as text.",
                    )
            else:
                invoice_text = file_bytes.decode('utf-8', errors='ignore')

        if not invoice_text:
            if request.is_json:
                data = request.get_json(silent=True) or {}
                invoice_text = str(data.get('text', '') or '')
            else:
                invoice_text = request.form.get('text', '')

        # Sanitize input
        invoice_text = invoice_text.strip()[:10000]
        if len(invoice_text) < MIN_INVOICE_CHARS:
            return api_error(
                400, "text_too_short",
                "Invoice text too short. Please include product descriptions, "
                "HTS codes, values, and country of origin.",
            )

        # Optional entry facts drive the remedy router: without a liquidation
        # status we cannot know whether the correct vehicle is a PSC (pre-
        # liquidation) or a §1514 protest (post-liquidation, 180-day clock).
        def _entry_fact(key):
            v = request.form.get(key)
            if v is None and request.is_json:
                v = (request.get_json(silent=True) or {}).get(key)
            return v

        entry_facts = {
            "entry_date": _entry_fact("entry_date"),
            "liquidation_date": _entry_fact("liquidation_date"),
            "liquidation_status": _entry_fact("liquidation_status"),
        }

        # Log request (no invoice content for privacy)
        log.info(f"[ANALYZE] length={len(invoice_text)} chars")

        try:
            analysis = analyze_with_claude(invoice_text)
        except AIUnavailableError:
            log.warning("No valid ANTHROPIC_API_KEY — live analysis unavailable")
            return api_error(
                503, "ai_unavailable",
                "Live AI analysis is not configured on this deployment. "
                "Try a sample scenario instead.",
                demo_available=True,
            )
        except anthropic.RateLimitError as e:
            retry_after = "30"
            try:
                retry_after = e.response.headers.get("retry-after") or retry_after
            except Exception:
                pass
            return api_error(
                429, "rate_limited",
                "Too many analyses from this address. Please wait a minute and retry.",
                headers={"Retry-After": str(retry_after)},
            )
        except anthropic.APITimeoutError:
            return api_error(
                504, "model_timeout",
                "Analysis took too long. Try a shorter invoice or retry.",
            )
        except (anthropic.APIStatusError, anthropic.APIConnectionError, ModelResponseError) as e:
            log.error(f"Claude error: {e}")
            return api_error(502, "model_error", "The AI analysis failed. Please retry.")

        # Deterministic verification: every model claim is recomputed against
        # the official USITC schedule BEFORE the protest letter is generated,
        # so the legal artifact only ever contains verified numbers.
        analysis = verify_findings(analysis)
        remedy_summary = build_remedy_summary(**entry_facts)
        analysis['remedy_summary'] = remedy_summary
        # White-label (Enterprise/pilot): only an API-keyed firm gets its name
        # on the draft — anonymous callers can't forge letterhead.
        analysis['protest_letter'] = generate_protest_letter(
            analysis.get('findings', []),
            analysis.get('total_savings', 0),
            analysis.get('fta_type'),
            remedy_summary=remedy_summary,
            preparer_firm=firm,
        )
        if firm:
            analysis['white_label'] = {"preparer_firm": _sanitize_firm_name(firm)}
        analysis['meta'] = {
            "demo": False,
            "model": CLAUDE_MODEL,
            "latency_ms": int((time.time() - started) * 1000),
        }
        db.record_audit(
            "analyze", firm=firm,
            findings=len(analysis.get('findings') or []),
            verified_savings=analysis.get('total_savings'),
            meta={"model": CLAUDE_MODEL,
                  "latency_ms": analysis['meta']["latency_ms"]})
        return jsonify(analysis)

    except Exception as e:
        log.exception(f"Error in /analyze: {e}")
        return api_error(500, "internal_error", "Something went wrong. Please retry.")


@app.route('/api/analyze-batch', methods=['POST'])
def analyze_batch():
    """Deterministic bulk screen for brokers: 1-100 entry lines audited
    against the USITC schedule + curated patterns. Zero Claude calls.

    Accepts either JSON rows (the original contract) or a multipart CBP Form
    7501 PDF (`file` field) — the entry summary is parsed to ES-003 rows and
    run through the identical audit, so brokers can drop the 7501 straight in
    instead of hand-building a CSV."""
    source = None
    if request.files and 'file' in request.files:
        file_bytes = request.files['file'].read()
        if not file_bytes.startswith(b'%PDF-'):
            return api_error(
                422, "unreadable_file",
                "We couldn't read this file. Upload a CBP Form 7501 PDF, "
                "or send JSON rows.",
            )
        try:
            parsed = parse_7501(file_bytes)
        except Form7501Error as e:
            return api_error(422, e.code, e.message)
        payload = {"rows": parsed["rows"]}
        source = {
            "type": "7501_pdf",
            "entry_no": parsed["header"].get("entry_no"),
            "rows_parsed": len(parsed["rows"]),
            "warnings": parsed["warnings"],
        }
    else:
        payload = request.get_json(silent=True)

    try:
        result = run_batch_audit(payload)
    except BatchValidationError as e:
        return api_error(400, e.code, e.message)
    if source is not None:
        result["source"] = source
    summary = result.get("summary") or {}
    db.record_audit(
        "analyze-batch", firm=api_key_firm(),
        rows=summary.get("rows"), findings=summary.get("flagged"),
        verified_savings=summary.get("total_estimated_exposure"),
        meta={"source_type": (source or {}).get("type", "json_rows")})
    return jsonify(result)


# 2026 user-fee figures (19 CFR 24.23/24.24, FY2026 adjusted amounts):
# Merchandise Processing Fee 0.3464% ad valorem, min $33.58 / max $651.50;
# Harbor Maintenance Fee 0.125%, ocean shipments only.
MPF_RATE = 0.3464
MPF_MIN = 33.58
MPF_MAX = 651.50
HMF_RATE = 0.125


@app.route('/api/landed-cost', methods=['GET'])
def landed_cost():
    code = request.args.get('code', '').strip()
    origin = request.args.get('origin', '').strip()
    mode = (request.args.get('mode', 'ocean').strip().lower() or 'ocean')
    if mode not in ('ocean', 'air'):
        mode = 'ocean'
    try:
        value = float(request.args.get('value', ''))
    except (TypeError, ValueError):
        value = 0.0
    if not code or value <= 0:
        return api_error(400, "invalid_params", "Provide code and a positive value.")

    rec = lookup_hts(code)
    if rec is None:
        return api_error(
            404, "code_not_found",
            f"HTS code {code} not found in the USITC schedule.",
            found=False,
        )

    mfn_rate = rec.get("general_rate")
    mfn_raw = rec.get("general_raw", "")
    if mfn_rate is None:
        # Unparseable rate line (e.g. compound units) — duty estimated at 0,
        # raw text surfaced so the caller sees what the schedule says.
        mfn_rate = 0.0
    mfn_duty = round(value * mfn_rate / 100.0, 2)

    s301_rate, s301_estimated = get_section_301(code, origin)
    s301_duty = round(value * s301_rate / 100.0, 2)
    if s301_estimated:
        s301_note = (
            "Estimate — Section 301 coverage for this code could not be "
            "verified at line level; confirm before relying on it."
        )
    elif s301_rate > 0:
        s301_note = "Line-level per the USITC China Tariffs table."
    else:
        s301_note = None

    mpf = round(min(max(value * MPF_RATE / 100.0, MPF_MIN), MPF_MAX), 2)
    hmf = round(value * HMF_RATE / 100.0, 2) if mode == 'ocean' else 0.0

    total = round(mfn_duty + s301_duty + mpf + hmf, 2)

    fta = None
    fta_name, fta_rate = fta_rate_for_code(code, origin)
    if fta_rate is None and origin:
        country_name, country_rate, _ = check_fta(origin)
        if country_name is not None:
            fta_name, fta_rate = country_name, country_rate
    if fta_name is not None and fta_rate is not None:
        _, _, fta_form = check_fta(origin)
        fta_duty = round(value * fta_rate / 100.0, 2)
        duty_with_fta = round(fta_duty + s301_duty + mpf + hmf, 2)
        fta = {
            "eligible": True,
            "name": fta_name,
            "rate": fta_rate,
            "form": fta_form or "Importer certification",
            "duty_with_fta": duty_with_fta,
            "savings": round(total - duty_with_fta, 2),
        }

    response = jsonify({
        "found": True,
        "code": rec.get("code", code),
        "matched_note": rec.get("note"),
        "description": rec.get("description"),
        "origin": origin,
        "value": value,
        "mode": mode,
        "breakdown": {
            "mfn_rate": mfn_rate, "mfn_duty": mfn_duty, "mfn_rate_raw": mfn_raw,
            "section_301_rate": s301_rate, "section_301_duty": s301_duty,
            "section_301_note": s301_note,
            "mpf_rate": MPF_RATE, "mpf": mpf, "mpf_min": MPF_MIN, "mpf_max": MPF_MAX,
            "hmf_rate": HMF_RATE, "hmf": hmf,
        },
        "total_landed_duty": total,
        "effective_rate": round(total / value * 100.0, 2),
        "fta": fta,
        "disclaimer": "Estimate from the official USITC HTS 2026 schedule. "
                      "Not customs advice; verify with a licensed broker.",
    })
    # Deterministic per query string → safe to cache hard at the CDN.
    response.headers["Cache-Control"] = "public, s-maxage=86400, stale-while-revalidate=604800"
    return response


@app.route('/api/hs2028-check', methods=['GET'])
def hs2028_check_one():
    """Will this code survive the Jan 1, 2028 HS renumbering? Free, from the
    WCO correlation tables — no competitor ships this yet."""
    code = (request.args.get('code') or '').strip()
    if not code:
        return api_error(400, "missing_code", "Pass ?code= with a 6/8/10-digit HTS code.")
    result = hs2028_check_code(code)
    if result.get("status") == "invalid":
        return api_error(400, "invalid_code", result["message"])
    response = jsonify(result)
    response.headers["Cache-Control"] = "public, s-maxage=86400, stale-while-revalidate=604800"
    return response


@app.route('/api/hs2028-check-batch', methods=['POST'])
def hs2028_check_many():
    """Batch readiness screen: {"codes": [...]} up to 500."""
    data = request.get_json(silent=True) or {}
    codes = data.get('codes')
    if not isinstance(codes, list) or not codes:
        return api_error(400, "missing_codes", 'Send JSON {"codes": ["8471.30.0100", ...]}.')
    if len(codes) > 500:
        return api_error(400, "too_many_codes", "Maximum 500 codes per request.")
    return jsonify(hs2028_check_codes([str(c) for c in codes]))


_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _forward_lead(payload):
    """Best-effort push to a durable inbox (Slack-compatible or any JSON
    webhook) so leads survive ephemeral serverless logs. Configure
    LEADS_WEBHOOK_URL in the environment; without it we fall back to logging
    only. Never blocks or fails the user-facing request."""
    url = os.getenv("LEADS_WEBHOOK_URL", "").strip()
    if not url:
        return False
    try:
        import urllib.request
        lines = [f"*New TariffCheck lead* — {payload.get('source') or 'site'}"]
        for k in ("email", "firm", "entries_per_month", "software", "context"):
            if payload.get(k):
                lines.append(f"{k}: {payload[k]}")
        body = json.dumps({"text": "\n".join(lines), "lead": payload}).encode()
        req = urllib.request.Request(
            url, data=body, headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=4)
        return True
    except Exception:
        log.exception("lead webhook forward failed")
        return False


@app.route('/api/leads', methods=['POST'])
def leads():
    """Email capture with broker-qualification fields. Every lead is logged
    AND forwarded to LEADS_WEBHOOK_URL (Slack/webhook) so a brokerage
    principal requesting access can never silently evaporate with log
    retention."""
    data = request.get_json(silent=True) or {}

    # Honeypot: real users never fill the hidden "website" field.
    if str(data.get('website', '') or '').strip():
        return jsonify({"ok": True, "message": "Thanks — we'll be in touch."})

    email = str(data.get('email', '') or '').strip()
    if not _EMAIL_RE.match(email):
        return api_error(400, "invalid_email", "Provide a valid email address.")

    payload = {
        "event": "lead.captured",
        "email": email,
        "source": str(data.get('source', '') or '')[:100],
        "context": str(data.get('context', '') or '')[:500],
        "firm": str(data.get('firm', '') or '')[:200],
        "entries_per_month": str(data.get('entries_per_month', '') or '')[:50],
        "software": str(data.get('software', '') or '')[:100],
    }
    payload["forwarded"] = _forward_lead(payload)
    payload["persisted"] = db.record_lead(payload)
    log.info(json.dumps(payload))
    return jsonify({"ok": True, "message": "Thanks — we'll be in touch."})


MOCK_DEMOS = {
    "1": {
        "findings": [{
            "hts_code": "9403.90.8040",
            "description": "Executive office chairs, adjustable height, metal base, fabric upholstery",
            "current_rate": 5.3,
            "suggested_code": "9403.10.0000",
            "suggested_rate": 0.0,
            "declared_value": 64000,
            "savings": 3392,
            "explanation": "Metal-frame office chairs are specifically provided for under HTS 9403.10 (metal furniture of a kind used in offices) at 0% duty. The importer used the catch-all 9403.90 at 5.3%. Additionally, as goods of Mexican origin, USMCA provides duty-free treatment under 19 U.S.C. 4531. The importer failed to claim this FTA preference."
        }],
        "total_savings": 3392, "fta_eligible": True, "fta_type": "USMCA", "country_of_origin": "Mexico",
        "protest_letter": "To: U.S. Customs and Border Protection\nPort Director, Port of Houston\n\nRe: Protest of Tariff Classification — Entry No. ATL-2026-0087\n\nPursuant to 19 U.S.C. 1514(a)(2), the importer of record hereby protests the tariff classification of merchandise entered under HTS subheading 9403.90.8040 at a general duty rate of 5.3%.\n\nThe imported merchandise consists of adjustable-height executive office chairs with metal frames and bases. These goods are more specifically provided for under HTS subheading 9403.10.0000 (furniture of a kind used in offices, of metal) at a general duty rate of 0%. Furthermore, as goods of Mexican origin, the merchandise qualifies for duty-free preferential treatment under the United States-Mexico-Canada Agreement (USMCA) pursuant to 19 U.S.C. 4531.\n\nThe total overpayment of duties on this entry amounts to $3,392.00. We respectfully request that CBP reliquidate this entry under HTS 9403.10.0000 and refund all excess duties paid.\n\nRespectfully submitted,\nAuthorized Importer Representative\nTariffCheck Analysis System"
    },
    "2": {
        "findings": [
            {
                "hts_code": "6404.19.3560",
                "description": "Athletic shoes, outer sole rubber/plastics, textile upper, size 6-13",
                "current_rate": 37.5,
                "suggested_code": "6404.11.9060",
                "suggested_rate": 20.0,
                "declared_value": 44000,
                "savings": 7700,
                "explanation": "Footwear designed for athletic/sports use with rubber outer soles and textile uppers, valued over $12/pair, is specifically classified under HTS 6404.11.90 (sports footwear, valued over $12/pair) at 20%, not the general 6404.19 category at 37.5%. The product description, unit value ($22/pair) and intended use clearly indicate these are athletic shoes requiring the more specific classification."
            },
            {
                "hts_code": "6404.19.3960",
                "description": "Walking shoes, outer sole rubber, mesh textile upper, casual",
                "current_rate": 37.5,
                "suggested_code": "6404.11.9060",
                "suggested_rate": 20.0,
                "declared_value": 18000,
                "savings": 3150,
                "explanation": "Mesh-upper athletic-style walking shoes with rubber soles, valued over $12/pair, qualify as sports footwear under 6404.11.90 at 20%. The current classification under 6404.19 at 37.5% overstates duty by 17.5 percentage points. Note: CBP construes 'sports footwear' narrowly — athletic-use construction must be documented."
            }
        ],
        "total_savings": 10850, "fta_eligible": False, "fta_type": None, "country_of_origin": "Vietnam",
        "protest_letter": "To: U.S. Customs and Border Protection\nPort Director, Port of Savannah\n\nRe: Protest of Tariff Classification — Entry No. SAV-2026-2241\n\nPursuant to 19 U.S.C. 1514(a)(2), the importer protests the classification of two lines of footwear from Vietnam.\n\nItem 1: Athletic shoes classified under HTS 6404.19.3560 (37.5%) should be HTS 6404.11.2060 (sports footwear, 20%). Overpayment: $7,700.\nItem 2: Walking shoes classified under HTS 6404.19.9060 (37.5%) should be HTS 6404.11.2060 (20%). Overpayment: $3,150.\n\nBoth items were designed for athletic use as evidenced by the product specifications, mesh uppers, and cushioned athletic soles. HTS 6404.11 specifically covers sports footwear with rubber/plastic outer soles and textile uppers.\n\nTotal overpayment: $10,850. We respectfully request reliquidation and full refund.\n\nRespectfully submitted,\nAuthorized Importer Representative\nTariffCheck Analysis System"
    },
    "3": {
        "findings": [{
            "hts_code": "8419.89.9585",
            "description": "Industrial coffee roasting machines + replacement drum assemblies",
            "current_rate": 4.2,
            "suggested_code": "8419.89.1000",
            "suggested_rate": 0.0,
            "declared_value": 96400,
            "savings": 4049,
            "explanation": "The broker entered these roasters under the catch-all provision 8419.89.95 (other machinery, other) at 4.2%. Industrial machinery for the preparation or manufacture of food or drink — which coffee roasting equipment is — is specifically provided for under HTS 8419.89.10 at 0% (Free). GRI Rule 1: the more specific heading controls."
        }],
        "total_savings": 4049, "fta_eligible": False, "fta_type": None, "country_of_origin": "Colombia",
        "protest_letter": "To: U.S. Customs and Border Protection\nPort Director, Port of Miami\n\nRe: Protest — US-Colombia FTA Preference Not Applied\n\nPursuant to 19 U.S.C. 1514(a)(2), the importer protests the failure to apply US-Colombia Trade Promotion Agreement (CTPA) preferential duty rates.\n\nThe imported industrial coffee roasting equipment (HTS 8419.89.1000) originates in Colombia and qualifies for duty-free treatment under the US-Colombia CTPA, which entered into force May 15, 2012. The importer inadvertently paid the 4.5% general rate rather than the 0% CTPA preferential rate.\n\nCertificate of origin documentation confirming Colombian origin is attached. Total duties overpaid: $4,338.\n\nWe request reliquidation at the 0% CTPA preferential rate and full refund of excess duties.\n\nRespectfully submitted,\nAuthorized Importer Representative\nTariffCheck Analysis System"
    },
    "4": {
        "findings": [
            {
                "hts_code": "8708.99.8180",
                "description": "Precision-machined transmission housings, cast aluminum, CNC finished",
                "current_rate": 2.5,
                "suggested_code": "8708.99.8180",
                "suggested_rate": 0.0,
                "declared_value": 43500,
                "savings": 1088,
                "explanation": "Transmission housings originating in South Korea qualify for duty-free treatment under the US-Korea Free Trade Agreement (KORUS) pursuant to 19 U.S.C. 3805. The KORUS preferential rate for HTS 8708.99 is 0% vs the 2.5% general rate. KORUS preference was not claimed at entry."
            },
            {
                "hts_code": "8409.99.9190",
                "description": "Engine components — cylinder liners and valve assemblies, automotive",
                "current_rate": 2.5,
                "suggested_code": "8409.99.9190",
                "suggested_rate": 0.0,
                "declared_value": 31500,
                "savings": 788,
                "explanation": "Engine components of South Korean origin qualify for KORUS duty-free treatment. The 2.5% general rate applied at entry should be 0% under KORUS. Certification of origin required."
            }
        ],
        "total_savings": 1970, "fta_eligible": True, "fta_type": "KORUS", "country_of_origin": "South Korea",
        "protest_letter": "To: U.S. Customs and Border Protection\nPort Director, Port of Savannah\n\nRe: Protest — KORUS FTA Preferential Treatment Not Applied\n\nPursuant to 19 U.S.C. 1514(a)(2), the importer protests the failure to apply KORUS FTA preferential rates.\n\nItem 1: HTS 8708.99.8180 — KORUS rate 0% vs general 2.5%. Overpayment: $1,088.\nItem 2: HTS 8483.40.5000 — KORUS rate 0% vs general 2.8%. Overpayment: $882.\n\nAll goods originate in South Korea as supported by attached KORUS certificates of origin. Total overpayment: $1,970.\n\nWe request reliquidation at KORUS preferential rates and full refund.\n\nRespectfully submitted,\nAuthorized Importer Representative\nTariffCheck Analysis System"
    },
    "5": {
        "findings": [
            {
                "hts_code": "8477.80.0000",
                "description": "Pharmaceutical tablet coating machines + fluid bed dryer/granulator systems",
                "current_rate": 3.1,
                "suggested_code": "8479.89.9499",
                "suggested_rate": 0.0,
                "declared_value": 203000,
                "savings": 6293,
                "explanation": "Pharmaceutical processing equipment (tablet coaters and fluid bed dryers) is more specifically classified under HTS 8479.89.9499 (other machinery for making pharmaceutical products) at 0% duty, not the plastics/rubber machinery category 8477.80 at 3.1%. The principal use of this equipment in pharmaceutical manufacturing governs its classification under GRI principal use rules."
            }
        ],
        "total_savings": 7105, "fta_eligible": False, "fta_type": None, "country_of_origin": "India",
        "protest_letter": "To: U.S. Customs and Border Protection\nPort Director, Port of Charleston\n\nRe: Protest of Tariff Classification — Entry No. CHS-2026-4489\n\nPursuant to 19 U.S.C. 1514(a)(2), the importer protests the classification of pharmaceutical processing equipment under HTS 8477.80.0000 at 3.5%.\n\nThe imported machinery consists of GMP-compliant tablet coating machines and fluid bed dryer/granulator systems used exclusively in pharmaceutical manufacturing. Under GRI principal use rules and Additional U.S. Note 1 to Chapter 84, equipment designed principally for pharmaceutical production is classified under HTS 8479.89.9499 at 0%.\n\nThe importer provides pharmaceutical production contracts and FDA facility registration as evidence of principal use. Total overpayment: $7,105.\n\nWe request reliquidation under HTS 8479.89.9499 and full refund of excess duties.\n\nRespectfully submitted,\nAuthorized Importer Representative\nTariffCheck Analysis System"
    },
    "6": {
        "findings": [
            {
                "hts_code": "9403.60.8040",
                "description": "Kitchen cabinet sets, solid wood shaker style, 36 sets",
                "current_rate": 0.0,
                "section_301_rate": 0.0,
                "total_current_rate": 0.0,
                "suggested_code": "9403.40.9060",
                "suggested_rate": 0.0,
                "section_301_applies_suggested": False,
                "total_suggested_rate": 0.0,
                "declared_value": 24480,
                "savings": 0,
                "classification_risk": True,
                "confidence": "high",
                "explanation": "Kitchen cabinets have a specific HTS code: 9403.40.9060. Using 9403.60.8040 (other wooden furniture) is a misclassification even though the rate is identical for Vietnam-origin goods. Incorrect classification creates audit exposure and could trigger CBP scrutiny on future shipments. Vietnam origin: no Section 301 applies, base rate is Free.",
                "legal_basis": "GRI Rule 1, Chapter 94 Note 2 — goods are classifiable in the most specific heading",
                "action_required": "Correct future entries to 9403.40.9060"
            },
            {
                "hts_code": "9403.90.8040",
                "description": "Cabinet hardware and installation brackets, parts",
                "current_rate": 4.3,
                "section_301_rate": 0.0,
                "total_current_rate": 4.3,
                "suggested_code": "8302.42.3065",
                "suggested_rate": 3.9,
                "section_301_applies_suggested": False,
                "total_suggested_rate": 3.9,
                "declared_value": 9000,
                "savings": 36,
                "classification_risk": False,
                "confidence": "medium",
                "explanation": "Cabinet installation brackets sold separately may be more correctly classified as base-metal furniture hardware under 8302.42.30 at 3.9% rather than furniture parts under 9403.90 at 4.3%. Small savings but correct classification is important.",
                "legal_basis": "Chapter 83 Note vs Chapter 94 Note 2 — parts sold separately may fall to Ch.83",
                "action_required": "Review with customs broker for binding ruling"
            }
        ],
        "total_savings": 36,
        "fta_eligible": False,
        "fta_type": None,
        "country_of_origin": "Vietnam",
        "section_301_applies": False,
        "section_301_rate": 0.0,
        "protest_deadline_note": "180 days from liquidation date per 19 U.S.C. §1514(a)(2)",
        "cape_eligible": False,
        "cape_note": "IEEPA refunds do not apply here.",
        "disclaimer": "TariffCheck analysis is for informational purposes only.",
        "protest_letter": "To: U.S. Customs and Border Protection\nPort Director, Port of Savannah\n\nRe: Classification Correction Notice — Vietnam-origin Kitchen Cabinets\n\nPursuant to 19 U.S.C. 1514(a)(2), the importer notes a classification discrepancy on recent entries of kitchen cabinets from Vietnam, currently entered under HTS 9403.60.8040 (other wooden furniture).\n\nUnder GRI Rule 1 and Chapter 94 Note 2, kitchen cabinets are specifically provided for under HTS 9403.40.9060 (wooden furniture of a kind used in kitchens). Although the base duty rate is 0% for both subheadings on Vietnam-origin goods (no Section 301 applies), classification under the most specific heading is required.\n\nThe importer requests reclassification of subject entries to HTS 9403.40.9060 to align with the official tariff schedule and reduce future audit exposure. Additionally, cabinet installation brackets (entered as 9403.90.8040 at 4.3%) may be more appropriately classified under HTS 8302.49.6055 at 3.9%; a binding ruling is recommended.\n\nTotal duty correction on hardware items: $36.\n\nRespectfully submitted,\nAuthorized Importer Representative\nTariffCheck Analysis System"
    },
    "7": {
        "findings": [
            {
                "hts_code": "9617.00.9000",
                "description": "Stainless steel insulated tumblers, 20oz and 30oz, powder coated",
                "current_rate": 7.2,
                "section_301_rate": 0.0,
                "total_current_rate": 7.2,
                "suggested_code": "7323.93.0060",
                "suggested_rate": 2.0,
                "section_301_applies_suggested": True,
                "total_suggested_rate": 27.0,
                "declared_value": 7250,
                "savings": 377,
                "classification_risk": False,
                "confidence": "high",
                "explanation": "Most stainless steel tumblers without a true vacuum seal are classified under 7323.93.0060 (stainless steel household articles) at 2% base rate, NOT 9617.00.9000 (vacuum flasks) at 7.2%. Crucially, 7323.93 sits on the SUSPENDED Section 301 List 4B — no additional China duty applies (verified at line level against the USITC China Tariffs table). The reclassification is a clean 5.2-point recovery: $377 on this entry.",
                "legal_basis": "GRI Rule 1, Chapter 96 Note; CBP administrative rulings on tumbler classification; USITC China Tariffs table (List 4B suspended)",
                "action_required": "Review with your customs broker — binding ruling recommended for recurring volumes"
            }
        ],
        "total_savings": 377,
        "fta_eligible": False,
        "fta_type": None,
        "country_of_origin": "China",
        "section_301_applies": False,
        "section_301_rate": 0.0,
        "protest_deadline_note": "180 days from liquidation date per 19 U.S.C. §1514(a)(2)",
        "cape_eligible": False,
        "cape_note": "IEEPA refunds do not apply here. Neither 9617.00.90 nor 7323.93 carries Section 301 (List 4B is suspended).",
        "disclaimer": "TariffCheck analysis is for informational purposes only.",
        "protest_letter": "To: U.S. Customs and Border Protection\nPort Director, Port of Long Beach\n\nRe: Protest of Tariff Classification — China-origin Stainless Tumblers\n\nPursuant to 19 U.S.C. 1514(a)(2), the importer protests the classification of stainless steel insulated tumblers under HTS 9617.00.9000 at 7.2%.\n\nThe imported merchandise consists of powder-coated, double-walled stainless steel tumblers without a true vacuum-seal mechanism. Per CBP administrative rulings, articles of this construction are more specifically classified under HTS 7323.93.0060 (stainless steel household articles, table/kitchen) at 2%. Even with Section 301 List 3 stacking (25%) on China-origin goods, the total effective rate of 27% under 7323.93 produces a net savings versus 7.2% under 9617 in cases where Section 301 does not apply to the 9617 classification.\n\nProduct sample, technical drawings, and supplier specification sheets are attached. The importer requests CBP confirm classification via binding ruling for future shipments. Total overpayment on this entry: $377.\n\nRespectfully submitted,\nAuthorized Importer Representative\nTariffCheck Analysis System"
    },
    "8": {
        "findings": [
            {
                "hts_code": "6109.90.1007",
                "description": "T-shirts, crew neck, fabric composition 60% cotton 40% polyester",
                "current_rate": 32.0,
                "section_301_rate": 0.0,
                "total_current_rate": 32.0,
                "suggested_code": "6109.10.0012",
                "suggested_rate": 16.5,
                "section_301_applies_suggested": False,
                "total_suggested_rate": 16.5,
                "declared_value": 8400,
                "savings": 1302,
                "classification_risk": False,
                "confidence": "high",
                "explanation": "A fabric that is 60% cotton and 40% polyester is classified by CHIEF WEIGHT under US tariff rules. Since cotton exceeds 50%, these are COTTON t-shirts under 6109.10 at 16.5%, NOT synthetic t-shirts under 6109.90 at 32%. This is one of the most common apparel misclassifications. Bangladesh has no Section 301. Savings: 15.5% on $8,400 = $1,302.",
                "legal_basis": "Additional U.S. Note 2 to Section XI — chief weight determines fiber classification",
                "action_required": "File CBP protest within 180 days of liquidation"
            }
        ],
        "total_savings": 1302,
        "fta_eligible": False,
        "fta_type": None,
        "country_of_origin": "Bangladesh",
        "section_301_applies": False,
        "section_301_rate": 0.0,
        "protest_deadline_note": "180 days from liquidation date per 19 U.S.C. §1514(a)(2)",
        "cape_eligible": False,
        "cape_note": "IEEPA refunds do not apply. Bangladesh is not subject to Section 301.",
        "disclaimer": "TariffCheck analysis is for informational purposes only.",
        "protest_letter": "To: U.S. Customs and Border Protection\nPort Director, Port of Savannah\n\nRe: Protest of Tariff Classification — Bangladesh-origin Cotton-Blend T-shirts\n\nPursuant to 19 U.S.C. 1514(a)(2), the importer protests the classification of crew-neck t-shirts under HTS 6109.90.1007 (t-shirts of man-made fibers) at 32%.\n\nThe imported merchandise has a verified fabric composition of 60% cotton, 40% polyester. Under Additional U.S. Note 2 to Section XI of the HTS, classification by chief weight controls: because cotton exceeds 50% by weight, these goods are properly classified under HTS 6109.10.0012 (t-shirts of cotton) at 16.5%.\n\nBangladesh is not subject to Section 301 tariffs. Mill certificates and fiber-weight test reports are attached as evidence of chief weight.\n\nTotal duty overpayment on this entry: $1,302. The importer respectfully requests reliquidation under HTS 6109.10.0012 and refund of excess duties.\n\nRespectfully submitted,\nAuthorized Importer Representative\nTariffCheck Analysis System"
    }
}

# Demo payloads go through the SAME deterministic verifier as live analyses,
# at import time — demo numbers are provably schedule-consistent, and every
# demo response carries per-finding verified flags + a verification block.
# The protest letter is then REGENERATED from the verified findings, so a
# demo letter can never claim a figure the verification block just refuted.
for _demo in MOCK_DEMOS.values():
    verify_findings(_demo)
    _demo["protest_letter"] = generate_protest_letter(
        _demo.get("findings"), _demo.get("total_savings"), _demo.get("fta_type"))


@app.route('/demo', methods=['GET'])
@app.route('/api/demo', methods=['GET'])
def demo():
    return jsonify(MOCK_DEMOS["1"])

@app.route('/demo/<demo_id>', methods=['GET'])
@app.route('/api/demo/<demo_id>', methods=['GET'])
def demo_by_id(demo_id):
    if demo_id in MOCK_DEMOS:
        return jsonify(MOCK_DEMOS[demo_id])
    return jsonify(MOCK_DEMOS["1"])


@app.route('/health', methods=['GET'])
@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({
        "status": "ok",
        "version": VERSION,
        "service": "TariffCheck API",
        "hts_codes_loaded": len(HTS_RATES),
        "data_source": "USITC HTS 2026 (full schedule) + curated broker overlay",
        "claude_ready": bool(os.getenv("ANTHROPIC_API_KEY", "").startswith("sk-")),
        "model": CLAUDE_MODEL,
        "fta_countries": len(FTA_COUNTRIES),
    })


@app.route('/api/hts-lookup', methods=['POST'])
def hts_lookup():
    data = request.get_json(silent=True) or {}
    code = str(data.get('code', '')).strip()
    origin = str(data.get('country_of_origin', '')).strip()

    if not code:
        return jsonify({"error": "Provide an HTS code"}), 400

    result = lookup_hts(code)
    if not result:
        return jsonify({"error": f"HTS code {code} not found in the USITC schedule", "found": False}), 404

    section_301 = get_section_301_rate(code, origin)
    # Data-driven FTA check for this exact code, falling back to country-level
    fta_name, fta_rate = fta_rate_for_code(code, origin)
    fallback_name, fallback_rate, fta_form = check_fta(origin)
    if fta_name is None:
        fta_name, fta_rate = fallback_name, fallback_rate
    base_rate = result.get("general_rate")

    return jsonify({
        "found": True,
        "code": result.get("code", code),
        "matched_note": result.get("note"),
        "description": result.get("description"),
        "base_rate": base_rate,
        "base_rate_raw": result.get("general_raw", ""),
        "section_301_rate": section_301,
        "total_effective_rate": (base_rate + section_301) if base_rate is not None else None,
        "fta_eligible": fta_name is not None,
        "fta_name": fta_name,
        "fta_rate": fta_rate,
        "fta_form": fta_form if fta_name else None,
        "special_rates": result.get("special_rates", {}),
        "units": result.get("units", []),
        "chapter": result.get("chapter"),
        "notes": result.get("notes", "")
    })


@app.route('/api/hts-search', methods=['GET'])
def hts_search():
    query = request.args.get('q', '').strip()
    if len(query) < 2:
        return jsonify({"error": "Query must be at least 2 characters", "results": []}), 400
    try:
        limit = min(int(request.args.get('limit', 25)), 50)
    except ValueError:
        limit = 25

    results = search_hts(query, limit=limit)
    return jsonify({
        "query": query,
        "count": len(results),
        "results": [
            {
                "code": r.get("code"),
                "description": r.get("description"),
                "general_rate": r.get("general_rate"),
                "general_rate_raw": r.get("general_raw", ""),
                "special_rates": r.get("special_rates", {}),
                "chapter": r.get("chapter"),
                "units": r.get("units", []),
            }
            for r in results
        ],
    })


# Built frontend (copied to public/ during the Vercel build; served by nginx
# in the Docker setup, so these routes are a fallback for SPA client routing).
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "public"


@app.route('/', methods=['GET'])
def index():
    if (FRONTEND_DIR / "index.html").is_file():
        return send_from_directory(FRONTEND_DIR, "index.html")
    return jsonify({
        "message": "TariffCheck API running",
        "version": VERSION,
        "endpoints": ["/health", "/demo", "/demo/<id>", "/analyze", "/api/hts-lookup", "/api/hts-search?q="]
    })


@app.route('/<path:path>', methods=['GET'])
def spa_fallback(path):
    """Serve static files from the built frontend; unknown non-API paths fall
    back to index.html so client-side routes (/hts-lookup, /results) work."""
    if path.startswith(("api/", "health", "demo", "analyze")):
        return jsonify({"error": "Not found"}), 404
    candidate = (FRONTEND_DIR / path).resolve()
    if candidate.is_file() and str(candidate).startswith(str(FRONTEND_DIR)):
        return send_from_directory(FRONTEND_DIR, path)
    if (FRONTEND_DIR / "index.html").is_file():
        return send_from_directory(FRONTEND_DIR, "index.html")
    return jsonify({"error": "Not found"}), 404


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    debug = os.environ.get('FLASK_DEBUG', '').lower() in ('1', 'true')
    log.info(f"Starting TariffCheck API v{VERSION} on port {port} — "
             f"{len(HTS_RATES)} HTS codes loaded, "
             f"Claude: {'ready' if os.getenv('ANTHROPIC_API_KEY', '').startswith('sk-') else 'demo mode'}")
    app.run(host='0.0.0.0', port=port, debug=debug)
