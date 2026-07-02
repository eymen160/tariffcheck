# TariffCheck — AI Customs Duty Auditor

> **Live:** https://tariffcheck-zeta.vercel.app · Born at **Hacklanta 2026**, built by Eymen Keyvan, Esat Sarac, Selcuk Kandemir

US importers overpay an estimated **$26 billion a year** in customs duties through HTS misclassification, unclaimed FTA preferences, and wrongly applied Section 301 rates — and misclassification drives ~42% of CBP penalties. TariffCheck is the AI misclassification auditor for importers and the customs brokers who file for them: it reads any invoice or batch of entry lines, audits every line with Claude, deterministically re-verifies each finding against the complete **29,755-code official USITC HTS 2026 schedule** that ships inside the product, and hands back a ready-to-file **19 U.S.C. §1514 protest letter**. We prepare the filing; you or your licensed broker files it.

## How It Works

1. **Upload** — a commercial invoice (PDF or pasted text), or a batch of entry lines for broker portfolio scans.
2. **AI audit** — Claude analyzes every line with the official USITC rates injected at inference time (grounding block + structured outputs): misclassifications, missed FTA/USMCA claims, Section 301 exposure, with a legal basis per finding.
3. **Deterministic USITC verification** — every finding is re-checked against the in-process 29,755-code schedule. Rates and savings are recomputed server-side; unverifiable findings are labeled, never hidden. A hallucinated number cannot reach the letter.
4. **Protest letter** — a ready-to-file §1514 letter generated from verified numbers only, for the importer of record or a licensed broker to file.

## Features

- **Invoice analysis** (`/api/analyze`) — PDF or text in, verified findings + protest letter out.
- **Batch audit** (`/api/analyze-batch`) — up to 100 entry lines per request, fully deterministic (no API key needed), built for brokers scanning client portfolios.
- **Landed-cost calculator** (`/api/landed-cost`) — MFN + Section 301 + MPF/HMF + FTA comparison for any code/origin/value, CDN-cacheable.
- **Free HTS lookup & search** (`/api/hts-lookup`, `/api/hts-search`) — the full USITC schedule, no paywall.
- **Savings dashboard** — client-side history of your audits and verified savings (localStorage; nothing stored server-side).
- **Brokers page** — the bulk-scan pitch for brokerage firms, with lead capture (`/api/leads`).
- **Demo scenarios** — 8 sample audits served only via explicit `demo_id` (no filename-based mocks).

## Architecture

| Layer | Technology |
|---|---|
| Backend | Python Flask; full 29,755-code USITC HTS 2026 schedule as a gzipped JSON DB loaded **in-process** (`backend/data/hts_db.json.gz`) — parsed MFN rates + per-program FTA special rates, no external DB |
| AI | Anthropic Claude (`claude-haiku-4-5` by default, `CLAUDE_MODEL` overridable) with structured outputs (JSON schema), prompt caching, and a per-invoice USITC grounding block |
| Verification | Deterministic server-side verifier — every AI finding's codes looked up in the USITC DB, rates and savings recomputed before any letter is generated |
| PDF parsing | pdfplumber (tables) + PyPDF2 (fallback) |
| Frontend | React 18 + Vite + React Router |
| Deploy | Vercel — static Vite build + Python serverless function (`api/index.py` exposes the Flask WSGI app). **Stateless**: no database, no persistent disk |

## API Overview

Full reference with request/response examples and error codes: **[docs/API.md](docs/API.md)**

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/health` | Service status, schedule size, Claude readiness |
| POST | `/api/analyze` | Audit one invoice (PDF/text/`demo_id`) → verified findings + protest letter |
| POST | `/api/analyze-batch` | Deterministic screen of 1–100 entry lines (broker feature) |
| GET | `/api/landed-cost` | Duty/fee breakdown for code + origin + value, with FTA comparison |
| POST | `/api/hts-lookup` | Duty rate + FTA eligibility for one code |
| GET | `/api/hts-search?q=` | Search the 29,755-code schedule by prefix or keywords |
| GET | `/api/demo/<1-8>` | Pre-built demo scenarios |
| POST | `/api/leads` | Stateless email capture |

## Run Locally

### Backend

```bash
cd backend
python3 -m venv .venv && ./.venv/bin/pip install -r requirements.txt
PORT=8000 ./.venv/bin/python app.py
```

`ANTHROPIC_API_KEY` is **optional**: without it, `/api/analyze` on real invoices returns a clear 503 (`ai_unavailable`), while the deterministic endpoints — batch audit, landed cost, HTS lookup/search, demos — all work fully offline against the bundled USITC schedule. To enable live AI analysis, `cp .env.example .env` and add your key.

### Frontend

```bash
cd frontend
npm install
npm run dev
# open http://localhost:5173 — /api/* is proxied to localhost:8000 by the Vite dev server
```

### Production build check

```bash
cd frontend && npm run build
```

## Deploy

Deployed on Vercel: static Vite build + a Python serverless function (`vercel.json` pins framework detection off — do not change). Set `ANTHROPIC_API_KEY` in the Vercel project env to enable live analysis. A `Dockerfile.combined` (nginx + gunicorn) also exists for container hosting:

```bash
docker build --platform linux/amd64 -f Dockerfile.combined -t tariffcheck .
docker run -p 80:80 -e ANTHROPIC_API_KEY=sk-... tariffcheck
```

## Team

| Name | Role |
|---|---|
| Eymen Keyvan | Full-Stack & Deployment |
| Esat Sarac | Backend & AI Integration |
| Selcuk Kandemir | Frontend & UI/UX |

## Legal

TariffCheck provides analysis assistance only — this is not legal or customs advice. We **prepare** classification audits and §1514 protest packages; the importer of record or a licensed customs broker reviews and **files** them. All HTS classifications should be verified by a licensed customs broker or attorney before any formal protest is filed with US Customs and Border Protection. The 180-day protest deadline under 19 U.S.C. §1514 applies uniformly to all entries.
