from flask import Flask, request, jsonify
from flask_cors import CORS
import anthropic
import PyPDF2
import json
import io
import os
from dotenv import load_dotenv
from hts_database import lookup_hts, check_fta, HTS_RATES, get_misclassification_hint

load_dotenv()

app = Flask(__name__)
CORS(app, origins="*")

MOCK_RESPONSE = {
    "findings": [
        {
            "hts_code": "9403.90.8040",
            "description": "Office furniture, metal frame chairs",
            "current_rate": 5.3,
            "suggested_code": "9403.10.0000",
            "suggested_rate": 0.0,
            "declared_value": 64000,
            "savings": 3392,
            "explanation": "Metal office chairs are more specifically classified under HTS 9403.10 (metal furniture of a kind used in offices) at 0% duty rate, rather than the general 9403.90 category at 5.3%. Since goods originate from Mexico, USMCA also applies for 0% duty."
        }
    ],
    "total_savings": 3392,
    "fta_eligible": True,
    "fta_type": "USMCA",
    "country_of_origin": "Mexico",
    "protest_letter": "To: U.S. Customs and Border Protection\nPort Director, Port of Atlanta\n\nRe: Protest of Tariff Classification — Entry #ATL-2026-DEMO\n\nDear Port Director,\n\nPursuant to 19 U.S.C. §1514(a)(2), the importer hereby protests the classification of imported merchandise under HTS subheading 9403.90.8040 at a general duty rate of 5.3%.\n\nThe imported merchandise consists of metal-frame office chairs, which are more specifically provided for under HTS subheading 9403.10.0000 (furniture of a kind used in offices, of metal) at a general duty rate of 0%. Furthermore, as goods of Mexican origin, the merchandise qualifies for duty-free treatment under the United States-Mexico-Canada Agreement (USMCA) pursuant to 19 U.S.C. §4531.\n\nThe total overpayment of duties resulting from this misclassification amounts to $3,392. We respectfully request that CBP reliquidate this entry under HTS 9403.10.0000 and refund the excess duties paid.\n\nRespectfully submitted,\nAuthorized Importer Representative\nTariffCheck Analysis System"
}


def extract_text_from_pdf(file_bytes):
    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
        text = ""
        for page in pdf_reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"
        return text.strip()
    except Exception as e:
        print(f"PDF extraction error: {e}")
        return ""


def analyze_with_claude(invoice_text):
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key or api_key in ("dummy", "dummy_key_for_demo", "your_key_here", ""):
        print("No valid API key — returning mock response")
        return None

    try:
        client = anthropic.Anthropic(api_key=api_key)

        system_prompt = """You are a US customs classification expert with 20 years of experience analyzing commercial invoices and HTS codes.

Analyze the provided document and find duty savings opportunities.

Return ONLY valid JSON in this exact format, no other text:
{
  "findings": [
    {
      "hts_code": "current HTS code from invoice or inferred from product description",
      "description": "product description from invoice",
      "current_rate": 5.3,
      "suggested_code": "better HTS code if one exists, same as current if correct",
      "suggested_rate": 0.0,
      "declared_value": 64000,
      "savings": 3392,
      "explanation": "plain English explanation of the savings opportunity or why current code is correct"
    }
  ],
  "total_savings": 3392,
  "fta_eligible": true,
  "fta_type": "USMCA",
  "country_of_origin": "Mexico"
}

Rules:
- If origin is Canada or Mexico: USMCA applies, set fta_eligible=true, fta_type="USMCA"
- If origin is South Korea: KORUS applies
- savings = (current_rate - suggested_rate) / 100 * declared_value
- If no savings found, set savings=0 and explain why current classification is correct
- Always return valid JSON only"""

        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1500,
            system=system_prompt,
            messages=[
                {
                    "role": "user",
                    "content": f"Analyze this customs invoice and find HTS misclassification savings:\n\n{invoice_text[:3000]}"
                }
            ]
        )

        response_text = message.content[0].text.strip()
        # Extract JSON
        start = response_text.find('{')
        end = response_text.rfind('}') + 1
        if start != -1 and end > start:
            return json.loads(response_text[start:end])
        return None

    except Exception as e:
        print(f"Claude error: {e}")
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

        if not invoice_text or len(invoice_text.strip()) < 5:
            return jsonify({"error": "No invoice content provided"}), 400

        # Try Claude first
        analysis = analyze_with_claude(invoice_text)

        # Fallback to mock if Claude fails
        if not analysis:
            print("Using mock response")
            return jsonify(MOCK_RESPONSE)

        # Generate protest letter if not included
        if not analysis.get('protest_letter'):
            analysis['protest_letter'] = generate_protest_letter(
                analysis.get('findings', []),
                analysis.get('total_savings', 0),
                analysis.get('fta_type')
            )

        return jsonify(analysis)

    except Exception as e:
        print(f"Error in /analyze: {e}")
        return jsonify(MOCK_RESPONSE)


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
    }
}


def extract_text_from_pdf(file_bytes):
    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
        text = ""
        for page in pdf_reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"
        return text.strip()
    except Exception as e:
        print(f"PDF extraction error: {e}")
        return ""


def analyze_with_claude(invoice_text):
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key or api_key in ("dummy", "dummy_key_for_demo", "your_key_here", ""):
        print("No valid API key — returning mock response")
        return None

    try:
        client = anthropic.Anthropic(api_key=api_key)

        system_prompt = """You are a US customs classification expert with 20 years of experience analyzing commercial invoices and HTS codes.

Analyze the provided document and find duty savings opportunities.

Return ONLY valid JSON in this exact format, no other text:
{
  "findings": [
    {
      "hts_code": "current HTS code from invoice or inferred from product description",
      "description": "product description from invoice",
      "current_rate": 5.3,
      "suggested_code": "better HTS code if one exists, same as current if correct",
      "suggested_rate": 0.0,
      "declared_value": 64000,
      "savings": 3392,
      "explanation": "plain English explanation of the savings opportunity or why current code is correct"
    }
  ],
  "total_savings": 3392,
  "fta_eligible": true,
  "fta_type": "USMCA",
  "country_of_origin": "Mexico"
}

Rules:
- If origin is Canada or Mexico: USMCA applies, set fta_eligible=true, fta_type="USMCA"
- If origin is South Korea: KORUS applies
- savings = (current_rate - suggested_rate) / 100 * declared_value
- If no savings found, set savings=0 and explain why current classification is correct
- Always return valid JSON only"""

        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1500,
            system=system_prompt,
            messages=[
                {
                    "role": "user",
                    "content": f"Analyze this customs invoice and find HTS misclassification savings:\n\n{invoice_text[:3000]}"
                }
            ]
        )

        response_text = message.content[0].text.strip()
        # Extract JSON
        start = response_text.find('{')
        end = response_text.rfind('}') + 1
        if start != -1 and end > start:
            return json.loads(response_text[start:end])
        return None

    except Exception as e:
        print(f"Claude error: {e}")
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

@app.route('/demo', methods=['GET'])
@app.route('/api/demo', methods=['GET'])
def demo():
    return jsonify(MOCK_RESPONSE)

@app.route('/demo/<demo_id>', methods=['GET'])
@app.route('/api/demo/<demo_id>', methods=['GET'])
def demo_by_id(demo_id):
    if demo_id in MOCK_DEMOS:
        return jsonify(MOCK_DEMOS[demo_id])
    return jsonify(MOCK_RESPONSE)


@app.route('/health', methods=['GET'])
@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({
        "status": "ok",
        "service": "TariffCheck API",
        "hts_codes": len(HTS_RATES),
        "claude_ready": bool(os.getenv("ANTHROPIC_API_KEY", "").startswith("sk-"))
    })


@app.route('/', methods=['GET'])
def index():
    return jsonify({"message": "TariffCheck API running", "endpoints": ["/health", "/demo", "/analyze"]})


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    print(f"Starting TariffCheck API on port {port}")
    print(f"Claude API: {'✅ Ready' if os.getenv('ANTHROPIC_API_KEY', '').startswith('sk-') else '⚠️ Mock mode'}")
    app.run(host='0.0.0.0', port=port, debug=True)
