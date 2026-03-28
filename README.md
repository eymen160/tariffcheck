# TariffCheck — AI Customs Duty Auditor

> **Hacklanta 2026** | Built by Eymen Keyvan, Esat Sarac, Selcuk Kandemir

US importers overpay **$26 billion** in customs duties every year due to HTS code misclassification. TariffCheck uses Claude AI to audit commercial invoices, find misclassified goods, and generate a ready-to-file CBP protest letter in under 30 seconds.

**Live Demo:** https://charming-deer-tariffcheck.cluster-se1-us.nexlayer.ai

---

## The Problem

Every imported shipment requires an HTS (Harmonized Tariff Schedule) code — a 10-digit number that determines the duty rate. With 17,000+ codes in the US schedule, misclassification is rampant. Importers overpay, rarely notice, and the 180-day protest window quietly expires.

## What TariffCheck Does

1. **Upload** a commercial invoice (PDF or paste text)
2. **AI Analysis** — Claude compares every HTS code against the official USITC tariff schedule, identifies misclassifications, and checks Free Trade Agreement eligibility (USMCA, KORUS, Colombia CTPA)
3. **Instant Results** — savings calculation per line item, total overpayment amount
4. **CBP Protest Letter** — ready-to-file letter citing 19 U.S.C. §1514, generated automatically

## Demo Scenarios

| # | Scenario | Origin | Savings |
|---|----------|--------|---------|
| 1 | Office furniture misclassified (9403.90 → 9403.10) | Mexico | $3,392 |
| 2 | Athletic footwear wrong category (6404.19 → 6404.11) | Vietnam | $10,850 |
| 3 | Coffee equipment — CTPA preference not claimed | Colombia | $4,338 |
| 4 | Auto parts — KORUS FTA preference missed | South Korea | $1,970 |
| 5 | Pharma machinery wrong chapter (8477 → 8479) | India | $7,105 |

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18 + Vite + React Router |
| Backend | Python Flask + Claude AI (claude-haiku-4-5) |
| PDF Parsing | pdfplumber (tables) + PyPDF2 (fallback) |
| Tariff Data | USITC HTS Schedule (50 codes) |
| Deployment | Nexlayer (combined nginx + gunicorn container) |

## Run Locally

### Backend
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env        # add your ANTHROPIC_API_KEY
PORT=8000 python3 app.py
```

### Frontend
```bash
cd frontend
npm install
npm run dev
# Open http://localhost:5173
```

The frontend proxies `/api/*` to `localhost:8000` via Vite dev server.

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Service status + Claude readiness |
| GET | `/api/demo/<1-5>` | Pre-built demo scenarios |
| POST | `/api/analyze` | Analyze invoice — JSON body `{text}` or multipart PDF |

## Docker (Production)

```bash
# Build combined image (nginx + gunicorn in one container)
docker build --platform linux/amd64 -f Dockerfile.combined -t tariffcheck .

# Run
docker run -p 80:80 -e ANTHROPIC_API_KEY=sk-... tariffcheck
```

## Team

| Name | Role |
|------|------|
| Eymen Keyvan | Full-Stack & Deployment |
| Esat Sarac | Backend & AI Integration |
| Selcuk Kandemir | Frontend & UI/UX |

## Legal

TariffCheck provides analysis assistance only. This is not legal advice. All HTS classifications should be verified by a licensed customs broker or attorney before filing a formal protest with US Customs and Border Protection. The 180-day protest deadline under 19 U.S.C. §1514 applies uniformly to all entries.
