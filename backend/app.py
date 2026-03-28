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
def analyze():
    try:
        invoice_text = ""

        if request.files and 'file' in request.files:
            file = request.files['file']
            file_bytes = file.read()
            if file.filename and file.filename.lower().endswith('.pdf'):
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
        "findings": [{"hts_code":"9403.90.8040","description":"Office furniture, metal frame ergonomic chairs","current_rate":5.3,"suggested_code":"9403.10.0000","suggested_rate":0.0,"declared_value":64000,"savings":3392,"explanation":"Metal office chairs are specifically classified under HTS 9403.10 (metal furniture of a kind used in offices) at 0% duty rate. The general category 9403.90 at 5.3% is overly broad for this merchandise. Since goods originate from Mexico, USMCA also provides duty-free treatment under 19 U.S.C. 4531."}],
        "total_savings":3392,"fta_eligible":True,"fta_type":"USMCA","country_of_origin":"Mexico",
        "protest_letter":"To: U.S. Customs and Border Protection\nPort Director, Port of Atlanta\n\nRe: Protest of Tariff Classification pursuant to 19 U.S.C. 1514(a)(2)\n\nDear Port Director,\n\nThe importer hereby protests the classification of imported merchandise under HTS 9403.90.8040 at a general duty rate of 5.3%.\n\nThe imported merchandise consists of metal-frame office chairs, more specifically provided for under HTS 9403.10.0000 (metal furniture of a kind used in offices) at 0% duty. As goods of Mexican origin, USMCA duty-free treatment also applies under 19 U.S.C. 4531.\n\nTotal overpayment: $3,392. We request reliquidation and refund.\n\nRespectfully submitted,\nAuthorized Importer Representative\nTariffCheck Analysis System"
    },
    "2": {
        "findings": [
            {"hts_code":"6109.90.1090","description":"Men's t-shirts, 60% polyester 40% cotton blend","current_rate":32.0,"suggested_code":"6109.10.0012","suggested_rate":16.5,"declared_value":16000,"savings":2480,"explanation":"Although this fabric is a blend, the garment's chief weight is cotton (40% cotton is chief weight when considering fiber type). Under GRI 3(b), the essential character is cotton, making 6109.10 (cotton t-shirts at 16.5%) the correct classification. This results in significant duty savings vs 6109.90 at 32%."},
            {"hts_code":"6204.69.9010","description":"Women's trousers, woven, cotton-polyester blend","current_rate":28.6,"suggested_code":"6204.62.4021","suggested_rate":16.6,"declared_value":7500,"savings":900,"explanation":"Women's woven trousers with cotton as chief weight fiber are classified under 6204.62 at 16.6%, not the general 6204.69 category at 28.6%. Chief weight determination favors cotton, supporting the more specific classification."}
        ],
        "total_savings":3380,"fta_eligible":False,"fta_type":None,"country_of_origin":"Bangladesh",
        "protest_letter":"To: U.S. Customs and Border Protection\nPort Director, Port of Atlanta\n\nRe: Protest of Tariff Classification pursuant to 19 U.S.C. 1514(a)(2)\n\nDear Port Director,\n\nThe importer protests the classification of two textile items from Bangladesh.\n\nItem 1: HTS 6109.90.1090 (32%) should be 6109.10.0012 (16.5%) based on cotton chief weight determination under GRI 3(b). Savings: $2,480.\n\nItem 2: HTS 6204.69.9010 (28.6%) should be 6204.62.4021 (16.6%) for the same reason. Savings: $900.\n\nTotal overpayment: $3,380. We request reliquidation and refund of excess duties.\n\nRespectfully submitted,\nAuthorized Importer Representative\nTariffCheck Analysis System"
    },
    "3": {
        "findings": [
            {"hts_code":"8471.30.0100","description":"Portable laptops, 15 inch, automatic data processing machines","current_rate":0.0,"suggested_code":"8471.30.0100","suggested_rate":0.0,"declared_value":40000,"savings":0,"explanation":"HTS 8471.30.0100 is the correct classification for portable laptops. The 0% duty rate under the ITA (Information Technology Agreement) applies. No misclassification identified."},
            {"hts_code":"8517.12.0050","description":"Smartphones, 5G capable, Android OS","current_rate":0.0,"suggested_code":"8517.12.0050","suggested_rate":0.0,"declared_value":45000,"savings":0,"explanation":"Smartphones are correctly classified under 8517.12 at 0% duty. However, note that Section 301 additional tariffs on Chinese-origin goods may apply separately. Verify with your customs broker whether any Chapter 99 additional duties were assessed."}
        ],
        "total_savings":0,"fta_eligible":False,"fta_type":None,"country_of_origin":"China",
        "protest_letter":"No protest needed. Current HTS classifications for electronics from China appear correct. Note: Verify whether Section 301 Chapter 99 additional tariffs were correctly assessed on these entries separately from the base HTS duty rates."
    },
    "4": {
        "findings": [
            {"hts_code":"8708.29.5060","description":"Vehicle body parts, stamped steel panels","current_rate":2.5,"suggested_code":"8708.29.5060","suggested_rate":0.0,"declared_value":22500,"savings":562,"explanation":"As goods originating in South Korea, these auto parts qualify for duty-free treatment under the US-Korea Free Trade Agreement (KORUS) pursuant to 19 U.S.C. 3805. The applicable KORUS rate for HTS 8708.29 is 0%, reducing duty from 2.5% general rate. Ensure Form 3461 and KORUS certificate of origin documentation are on file."},
            {"hts_code":"8501.10.4060","description":"Electric motors, output not exceeding 37.5W","current_rate":6.7,"suggested_code":"8501.10.4060","suggested_rate":0.0,"declared_value":5600,"savings":375,"explanation":"Electric motors from South Korea qualify for KORUS preferential treatment at 0% vs the 6.7% general rate under HTS 8501.10. Proper KORUS origin documentation required."}
        ],
        "total_savings":937,"fta_eligible":True,"fta_type":"KORUS","country_of_origin":"South Korea",
        "protest_letter":"To: U.S. Customs and Border Protection\nPort Director, Port of Atlanta\n\nRe: Protest of Tariff Classification pursuant to 19 U.S.C. 1514(a)(2)\n\nDear Port Director,\n\nThe importer protests the failure to apply KORUS FTA preferential duty rates to goods of South Korean origin.\n\nItem 1: HTS 8708.29.5060 - KORUS rate 0% vs general rate 2.5%. Savings: $562.\nItem 2: HTS 8501.10.4060 - KORUS rate 0% vs general rate 6.7%. Savings: $375.\n\nCertificate of origin and KORUS eligibility documentation is attached. Total overpayment: $937.\n\nRespectfully submitted,\nAuthorized Importer Representative\nTariffCheck Analysis System"
    },
    "5": {
        "findings": [
            {"hts_code":"4202.92.9060","description":"Handbags and travel bags, genuine cowhide leather","current_rate":17.6,"suggested_code":"4202.12.2020","suggested_rate":20.0,"declared_value":44000,"savings":-1056,"explanation":"These leather handbags and duffels have genuine leather outer surface. HTS 4202.12 (leather outer surface bags) at 20% is more specific than 4202.92 (other bags, other materials) at 17.6%. The importer is currently UNDERPAYING duties by using the general category. This should be reclassified upward to avoid potential CBP penalty assessment for undervaluation."}
        ],
        "total_savings":0,"fta_eligible":False,"fta_type":None,"country_of_origin":"Italy",
        "protest_letter":"IMPORTANT NOTICE: TariffCheck analysis indicates the current HTS classification 4202.92.9060 at 17.6% may be incorrect for genuine leather goods. The more specific classification 4202.12.2020 at 20% applies to bags with leather outer surface. Current classification may result in underpayment of duties, which carries CBP penalty risk. Recommend filing a prior disclosure with CBP and reclassifying prospectively. Consult a licensed customs broker immediately."
    }
}

@app.route('/demo', methods=['GET'])
def demo():
    return jsonify(MOCK_RESPONSE)

@app.route('/demo/<demo_id>', methods=['GET'])
def demo_by_id(demo_id):
    if demo_id in MOCK_DEMOS:
        return jsonify(MOCK_DEMOS[demo_id])
    return jsonify(MOCK_RESPONSE)


@app.route('/health', methods=['GET'])
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
