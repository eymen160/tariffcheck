# TariffCheck — AI Customs Duty Auditor
**Hacklanta 2026 |OBIM team- Finance Track**

US importers overpay $26 billion in customs duties annually due to HTS misclassification. TariffCheck finds the errors and generates a ready-to-file CBP protest letter in 30 seconds.

## What it does
Upload a commercial invoice → AI compares HTS codes against the official USITC tariff schedule → finds misclassifications → calculates savings → generates CBP protest letter citing 19 U.S.C. 1514.

## Stack
- Frontend: React + Vite
- Backend: Python Flask + Claude AI
- Database: USITC HTS tariff schedule (50 codes)
- Deploy: Nexlayer

## Run locally

### Backend
```bash
cd backend
pip3 install -r requirements.txt
cp .env.example .env
# Add your ANTHROPIC_API_KEY to .env
PORT=8000 python3 app.py
```

### Frontend
```bash
cd frontend
npm install
npm run dev
# Open http://localhost:5173
```

## API Endpoints
- `GET /health` — backend status
- `GET /demo` — sample analysis (Mexico furniture, $3,392 savings)
- `GET /demo/1` through `/demo/5` — 5 different trade scenarios
- `POST /analyze` — analyze your own invoice (JSON or PDF upload)

## Demo Scenarios
1. Mexican office furniture — USMCA + misclassification = $3,392 savings
2. Bangladesh clothing — cotton chief weight = $3,380 savings
3. China electronics — correct codes, Section 301 note
4. South Korea auto parts — KORUS FTA = $937 savings
5. Italy leather goods — underpayment warning

## Legal
TariffCheck provides analysis assistance only. Consult a licensed customs broker before filing formal protests with CBP. Protest deadline: 180 days from liquidation per 19 U.S.C. 1514.
