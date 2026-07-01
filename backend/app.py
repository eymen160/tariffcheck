from flask import Flask, request, jsonify
from flask_cors import CORS
import anthropic
import PyPDF2
import pdfplumber
import json
import logging
import re
import io
import os
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
)

load_dotenv()

VERSION = "3.0.0"
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-haiku-4-5")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
log = logging.getLogger("tariffcheck")

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB upload cap
CORS(app, origins="*")

DEMO_MODE_RESPONSE = {
    "error": "demo_mode",
    "message": "TariffCheck AI analysis is temporarily unavailable. Please try again or use a demo scenario.",
    "demo_available": True,
    "findings": [],
    "total_savings": 0
}

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

HTS_CODE_RE = re.compile(r"\b(\d{4}\.\d{2}(?:\.\d{2}){0,2}|\d{4}\.\d{2}\.\d{4}|\d{8,10})\b")


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
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key or api_key in ("dummy", "dummy_key_for_demo", "your_key_here", ""):
        log.warning("No valid ANTHROPIC_API_KEY — returning demo mode")
        return None

    try:
        client = anthropic.Anthropic(api_key=api_key)

        grounding = build_grounding_block(invoice_text)

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

        if message.stop_reason == "refusal":
            log.warning("Claude declined the request (stop_reason=refusal)")
            return None
        return json.loads(message.content[0].text)

    except Exception as e:
        log.error(f"Claude error: {e}")
        return None


def generate_protest_letter(findings, total_savings, fta_type=None):
    if not findings or total_savings == 0:
        return "No protest needed — current classification appears correct."

    items = "\n".join([
        f"- HTS {f.get('hts_code')} → {f.get('suggested_code')} (save ${f.get('savings', 0):,.0f})"
        for f in findings if f.get('savings', 0) > 0
    ])

    fta_text = ""
    if fta_type:
        fta_text = f"Furthermore, as goods qualifying under {fta_type}, duty-free treatment applies. "

    return f"""To: U.S. Customs and Border Protection
Port Director

Re: Protest of Tariff Classification

Dear Port Director,

Pursuant to 19 U.S.C. §1514(a)(2), the importer hereby protests the tariff classification of imported merchandise and requests reliquidation of the affected entries.

The following misclassifications were identified:
{items}

{fta_text}The total overpayment of duties amounts to ${total_savings:,.2f}. We respectfully request that CBP reliquidate these entries under the correct HTS classifications and refund the excess duties paid within the statutory timeframe.

Respectfully submitted,
Authorized Importer Representative
TariffCheck Analysis System"""


@app.route('/analyze', methods=['POST'])
@app.route('/api/analyze', methods=['POST'])
def analyze():
    try:
        invoice_text = ""

        if request.files and 'file' in request.files:
            file = request.files['file']
            file_bytes = file.read()
            if file.filename and file.filename.lower().endswith('.pdf'):
                # Route demo PDFs to mock responses directly
                fname = file.filename.lower()
                if 'furniture' in fname or 'mexico' in fname or 'demo1' in fname:
                    return jsonify(MOCK_DEMOS["1"])
                elif 'footwear' in fname or 'vietnam' in fname or 'demo2' in fname:
                    return jsonify(MOCK_DEMOS["2"])
                elif 'coffee' in fname or 'colombia' in fname or 'demo3' in fname:
                    return jsonify(MOCK_DEMOS["3"])
                elif 'autopart' in fname or 'korea' in fname or 'demo4' in fname:
                    return jsonify(MOCK_DEMOS["4"])
                elif 'pharma' in fname or 'india' in fname or 'demo5' in fname:
                    return jsonify(MOCK_DEMOS["5"])
                invoice_text = extract_text_from_pdf(file_bytes)
            else:
                invoice_text = file_bytes.decode('utf-8', errors='ignore')

        if not invoice_text:
            if request.is_json:
                data = request.get_json(silent=True) or {}
                invoice_text = data.get('text', '')
            else:
                invoice_text = request.form.get('text', '')

        # Sanitize input
        invoice_text = invoice_text.strip()[:10000]
        if len(invoice_text) < 20:
            return jsonify({"error": "Invoice text too short. Please include product descriptions, HTS codes, values, and country of origin."}), 400

        # Log request (no invoice content for privacy)
        log.info(f"[ANALYZE] length={len(invoice_text)} chars")

        analysis = analyze_with_claude(invoice_text)

        if not analysis:
            log.warning("Claude unavailable — returning demo mode notice")
            return jsonify(DEMO_MODE_RESPONSE), 503

        if not analysis.get('protest_letter'):
            analysis['protest_letter'] = generate_protest_letter(
                analysis.get('findings', []),
                analysis.get('total_savings', 0),
                analysis.get('fta_type')
            )

        return jsonify(analysis)

    except Exception as e:
        log.exception(f"Error in /analyze: {e}")
        return jsonify(DEMO_MODE_RESPONSE), 500


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
                "suggested_code": "6404.11.2060",
                "suggested_rate": 20.0,
                "declared_value": 44000,
                "savings": 7700,
                "explanation": "Footwear designed for athletic/sports use with rubber outer soles and textile uppers is specifically classified under HTS 6404.11 (sports footwear) at 20%, not the general 6404.19 category at 37.5%. The product description and intended use clearly indicate these are athletic shoes requiring the more specific classification."
            },
            {
                "hts_code": "6404.19.9060",
                "description": "Walking shoes, outer sole rubber, mesh textile upper, casual",
                "current_rate": 37.5,
                "suggested_code": "6404.11.2060",
                "suggested_rate": 20.0,
                "declared_value": 18000,
                "savings": 3150,
                "explanation": "Mesh-upper walking shoes with rubber soles qualify as sports footwear under 6404.11 at 20%. The current classification under 6404.19 at 37.5% overstates duty by 17.5 percentage points."
            }
        ],
        "total_savings": 10850, "fta_eligible": False, "fta_type": None, "country_of_origin": "Vietnam",
        "protest_letter": "To: U.S. Customs and Border Protection\nPort Director, Port of Savannah\n\nRe: Protest of Tariff Classification — Entry No. SAV-2026-2241\n\nPursuant to 19 U.S.C. 1514(a)(2), the importer protests the classification of two lines of footwear from Vietnam.\n\nItem 1: Athletic shoes classified under HTS 6404.19.3560 (37.5%) should be HTS 6404.11.2060 (sports footwear, 20%). Overpayment: $7,700.\nItem 2: Walking shoes classified under HTS 6404.19.9060 (37.5%) should be HTS 6404.11.2060 (20%). Overpayment: $3,150.\n\nBoth items were designed for athletic use as evidenced by the product specifications, mesh uppers, and cushioned athletic soles. HTS 6404.11 specifically covers sports footwear with rubber/plastic outer soles and textile uppers.\n\nTotal overpayment: $10,850. We respectfully request reliquidation and full refund.\n\nRespectfully submitted,\nAuthorized Importer Representative\nTariffCheck Analysis System"
    },
    "3": {
        "findings": [{
            "hts_code": "8419.89.1000",
            "description": "Industrial coffee roasting machines + replacement drum assemblies",
            "current_rate": 4.5,
            "suggested_code": "8419.89.1000",
            "suggested_rate": 0.0,
            "declared_value": 96400,
            "savings": 4338,
            "explanation": "The goods are correctly classified under HTS 8419.89.1000. However, the importer failed to claim US-Colombia Trade Promotion Agreement (CTPA) preferential duty-free treatment. As goods wholly originating in Colombia, these machines qualify for a 0% preferential rate under CTPA, reducing duties from 4.5% to 0%."
        }],
        "total_savings": 4338, "fta_eligible": True, "fta_type": "US-Colombia CTPA", "country_of_origin": "Colombia",
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
                "hts_code": "8483.40.5000",
                "description": "Gear boxes and speed reducers for automotive applications",
                "current_rate": 2.8,
                "suggested_code": "8483.40.5000",
                "suggested_rate": 0.0,
                "declared_value": 31500,
                "savings": 882,
                "explanation": "Gear boxes of South Korean origin qualify for KORUS duty-free treatment. The 2.8% general rate applied at entry should be 0% under KORUS. Certificate of origin required."
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
                "current_rate": 3.5,
                "suggested_code": "8479.89.9499",
                "suggested_rate": 0.0,
                "declared_value": 203000,
                "savings": 7105,
                "explanation": "Pharmaceutical processing equipment (tablet coaters and fluid bed dryers) is more specifically classified under HTS 8479.89.9499 (other machinery for making pharmaceutical products) at 0% duty, not the general 8477.80 category for plastics/rubber machinery at 3.5%. The principal use of this equipment in pharmaceutical manufacturing governs its classification under GRI principal use rules."
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
                "suggested_code": "8302.49.6055",
                "suggested_rate": 3.9,
                "section_301_applies_suggested": False,
                "total_suggested_rate": 3.9,
                "declared_value": 9000,
                "savings": 36,
                "classification_risk": False,
                "confidence": "medium",
                "explanation": "Cabinet installation brackets sold separately may be more correctly classified as hardware under 8302.49 (drawer slides/mounting hardware) at 3.9% rather than furniture parts under 9403.90 at 4.3%. Small savings but correct classification is important.",
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
                "explanation": "Most stainless steel tumblers are classified under 7323.93.0060 (stainless steel household articles) at 2% base rate, NOT 9617.00.9000 (vacuum flasks) at 7.2%. While the tumbler may be double-walled, CBP rulings generally require a true vacuum seal for 9617 classification. Under 7323.93, China Section 301 List 3 adds 25%, for a total of 27% — but this is still lower than 7.2% under 9617 if no Section 301 applies there. IMPORTANT: Verify whether the Section 301 rate applies to 9617 for your specific product before filing protest.",
                "legal_basis": "GRI Rule 1, Chapter 96 Note; CBP administrative rulings on tumbler classification",
                "action_required": "Verify with customs broker — binding ruling recommended for large volumes"
            }
        ],
        "total_savings": 377,
        "fta_eligible": False,
        "fta_type": None,
        "country_of_origin": "China",
        "section_301_applies": True,
        "section_301_rate": 25.0,
        "protest_deadline_note": "180 days from liquidation date per 19 U.S.C. §1514(a)(2)",
        "cape_eligible": False,
        "cape_note": "IEEPA refunds do not apply here. Section 301 tariffs remain in effect.",
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


@app.route('/', methods=['GET'])
def index():
    return jsonify({
        "message": "TariffCheck API running",
        "version": VERSION,
        "endpoints": ["/health", "/demo", "/demo/<id>", "/analyze", "/api/hts-lookup", "/api/hts-search?q="]
    })


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    debug = os.environ.get('FLASK_DEBUG', '').lower() in ('1', 'true')
    log.info(f"Starting TariffCheck API v{VERSION} on port {port} — "
             f"{len(HTS_RATES)} HTS codes loaded, "
             f"Claude: {'ready' if os.getenv('ANTHROPIC_API_KEY', '').startswith('sk-') else 'demo mode'}")
    app.run(host='0.0.0.0', port=port, debug=debug)
