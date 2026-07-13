#!/usr/bin/env python3
"""Build a real-world test dataset for TariffCheck from CBP CROSS rulings.

CROSS (rulings.cbp.gov) publishes every binding classification ruling CBP has
issued: a real product description and the HTS code CBP officially assigned.
That makes it ground truth — if TariffCheck disagrees with a recent ruling,
TariffCheck is wrong (or the schedule changed).

Outputs (in this directory):
  cross_rulings_dataset.json  — full records with ruling numbers for traceability
  batch_rows_1.json ...       — ready-to-POST bodies for /api/analyze-batch (<=100 rows each)
  invoice_batch_*.txt         — commercial-invoice-style text files for /api/analyze
"""
import gzip
import json
import random
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

HERE = Path(__file__).parent
DB_PATH = HERE.parent / "backend" / "data" / "hts_db.json.gz"
API = "https://rulings.cbp.gov/api/search"

# Diverse search terms so the dataset spans many chapters, not just apparel
TERMS = [
    "footwear", "furniture", "electronics", "motor vehicle parts", "steel",
    "plastic", "textile", "machinery", "toys", "lighting", "kitchen",
    "aluminum", "chemical", "medical device", "solar", "battery", "bicycle",
    "ceramic", "glassware", "handbag", "jewelry", "pump", "valve", "cable",
    "sporting goods", "hand tools", "fasteners", "pet products", "cosmetics",
    "luggage", "watches", "musical instruments", "safety equipment", "garden",
    "tableware", "stationery", "appliances", "HVAC", "bearings", "motors",
    "sensors", "LED", "textiles knit", "footwear rubber", "auto electronics",
    "furniture outdoor", "packaging", "filters", "power supply",
]
PER_TERM = 30
TARGET = 520


def load_hts_db():
    with gzip.open(DB_PATH) as f:
        return json.load(f)


def fetch(term, page=1, page_size=PER_TERM):
    qs = urllib.parse.urlencode({
        "term": term, "collection": "ALL", "pageSize": page_size,
        "page": page, "sortBy": "DATE_DESC",
    })
    req = urllib.request.Request(f"{API}?{qs}", headers={"User-Agent": "TariffCheck-test-data/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


SUBJECT_PREFIX = re.compile(
    r"^the tariff classification(?:,? (?:and )?[a-z /]+)* of ", re.IGNORECASE)

# Whitelist of real country names — an origin only counts if it validates here.
COUNTRIES = [
    "China", "Taiwan", "Hong Kong", "Macau", "Vietnam", "South Korea",
    "Japan", "India", "Indonesia", "Thailand", "Malaysia", "Philippines",
    "Singapore", "Cambodia", "Laos", "Myanmar", "Bangladesh", "Pakistan",
    "Sri Lanka", "Nepal", "Turkey", "Israel", "Jordan", "Saudi Arabia",
    "United Arab Emirates", "Germany", "France", "Italy", "Spain",
    "Portugal", "United Kingdom", "Ireland", "Netherlands", "Belgium",
    "Switzerland", "Austria", "Sweden", "Norway", "Denmark", "Finland",
    "Iceland", "Poland", "Czech Republic", "Slovakia", "Hungary", "Romania",
    "Bulgaria", "Greece", "Ukraine", "Russia", "Estonia", "Latvia",
    "Lithuania", "Slovenia", "Croatia", "Serbia", "Canada", "Mexico",
    "United States", "Brazil", "Argentina", "Chile", "Colombia", "Peru",
    "Ecuador", "Costa Rica", "Dominican Republic", "Guatemala", "Honduras",
    "El Salvador", "Nicaragua", "New Zealand", "Australia", "South Africa",
    "Egypt", "Morocco", "Tunisia", "Kenya", "Nigeria", "Ethiopia",
    "Afghanistan", "Somalia",
]
_ALIASES = {
    "korea": "South Korea", "republic of korea": "South Korea",
    "viet nam": "Vietnam", "usa": "United States", "u.s.a": "United States",
    "united states of america": "United States", "holland": "Netherlands",
    "burma": "Myanmar", "macao": "Macau", "great britain": "United Kingdom",
    "england": "United Kingdom", "uae": "United Arab Emirates",
    "russian federation": "Russia", "slovak republic": "Slovakia",
    "people's republic of china": "China", "czechia": "Czech Republic",
}
COUNTRY_LOOKUP = {c.lower(): c for c in COUNTRIES}
COUNTRY_LOOKUP.update(_ALIASES)

# After "from", stop the country phrase at punctuation, a connector
# ("and", "or"), or a second "from" — subjects like "...bags from China and
# two additional bags from Hong Kong" must yield only the first country.
COUNTRY_STOP = re.compile(r"[,;.]|\band\b|\bor\b|\bfrom\b")


def match_country(text):
    """Validate a candidate origin phrase against the whitelist (or None)."""
    t = text.strip()
    t = re.sub(r"\s*\([^)]*\)\s*$", "", t)      # drop trailing parenthetical
    t = re.sub(r"^the\s+", "", t, flags=re.IGNORECASE)
    t = t.strip(" .,;:'\"")
    return COUNTRY_LOOKUP.get(t.lower())


def parse_subject(subject):
    """'The tariff classification of a tote bag from South Korea'
       -> ('tote bag', 'South Korea')

    Only the FIRST country phrase after a 'from' is used, and it must
    validate against the whitelist; otherwise origin is None ('Various')."""
    origin = None
    desc = subject
    for m in re.finditer(r"\bfrom\s+", subject, flags=re.IGNORECASE):
        first = COUNTRY_STOP.split(subject[m.end():], maxsplit=1)[0]
        country = match_country(first)
        if country:
            origin = country
            desc = subject[: m.start()].rstrip(" ,")
            break
    desc = SUBJECT_PREFIX.sub("", desc).strip()
    desc = re.sub(r"^(a|an|the)\s+", "", desc, flags=re.IGNORECASE)
    return desc, origin


def normalize(code):
    return re.sub(r"\D", "", code)


def main():
    db = load_hts_db()
    rng = random.Random(2026)

    records, seen = [], set()
    for term in TERMS:
        try:
            data = fetch(term)
        except Exception as e:
            print(f"  ! {term}: {e}")
            continue
        for r in data.get("rulings", []):
            if "Classification" not in (r.get("categories") or ""):
                continue
            if r.get("operationallyRevoked"):
                continue
            num = r["rulingNumber"]
            if num in seen:
                continue
            desc, origin = parse_subject(r.get("subject", ""))
            if not desc or len(desc) < 4:
                continue
            for tariff in r.get("tariffs", [])[:1]:  # primary code per ruling
                digits = normalize(tariff)
                if len(digits) < 8:
                    continue
                # validate against the product's own 2026 USITC schedule
                found = digits in db or digits[:8] in db
                records.append({
                    "ruling_number": num,
                    "ruling_date": (r.get("rulingDate") or "")[:10],
                    "hts_code": tariff,
                    "in_2026_schedule": found,
                    "description": desc[:200],
                    "origin": origin,
                    "search_term": term,
                })
                seen.add(num)
        print(f"  {term}: total so far {len(records)}")
        time.sleep(0.4)
        if len(records) >= TARGET:
            break

    valid = [r for r in records if r["in_2026_schedule"]]
    print(f"\nFetched {len(records)} rulings, {len(valid)} with codes valid in the 2026 schedule")

    # deterministic realistic declared values
    for i, r in enumerate(valid):
        r["row_id"] = i + 1
        r["declared_value"] = rng.choice([1, 2, 5, 8, 10, 15, 25, 40, 60]) * 1000 + rng.randrange(0, 999)

    (HERE / "cross_rulings_dataset.json").write_text(json.dumps(valid, indent=2))

    # batch bodies for /api/analyze-batch (max 100 rows per request)
    for n, start in enumerate(range(0, len(valid), 100), 1):
        chunk = valid[start:start + 100]
        body = {"rows": [
            {"row_id": r["row_id"], "hts_code": r["hts_code"],
             "description": r["description"],
             "declared_value": r["declared_value"],
             **({"origin": r["origin"]} if r["origin"] else {})}
            for r in chunk
        ]}
        (HERE / f"batch_rows_{n}.json").write_text(json.dumps(body, indent=2))
        print(f"batch_rows_{n}.json: {len(chunk)} rows")

    # a few invoice-style text files grouped by origin for /api/analyze
    by_origin = {}
    for r in valid:
        if r["origin"]:
            by_origin.setdefault(r["origin"], []).append(r)
    top = sorted(by_origin.items(), key=lambda kv: -len(kv[1]))[:5]
    for origin, rows in top:
        rows = rows[:8]
        slug = re.sub(r"\W+", "_", origin.lower()).strip("_")
        lines = [
            "COMMERCIAL INVOICE", "",
            f"Seller: Global Exports Ltd. ({origin})",
            "Buyer: Peachtree Imports LLC, Atlanta, GA, USA",
            f"Country of Origin: {origin}",
            "Invoice Date: July 10, 2026",
            f"Invoice No: GX-2026-{rng.randrange(1000, 9999)}", "",
        ]
        total = 0
        for j, r in enumerate(rows, 1):
            total += r["declared_value"]
            lines += [
                f"Item {j}:",
                f"HTS Code: {r['hts_code']}",
                f"Description: {r['description']}",
                f"Total Declared Value: ${r['declared_value']:,.2f} USD",
                f"(Source: CBP ruling {r['ruling_number']}, {r['ruling_date']})", "",
            ]
        lines.append(f"Total Invoice Value: ${total:,.2f} USD")
        (HERE / f"invoice_batch_{slug}.txt").write_text("\n".join(lines))
        print(f"invoice_batch_{slug}.txt: {len(rows)} items")


if __name__ == "__main__":
    main()
