#!/usr/bin/env python3
"""Replace synthetic declared values with real US import unit values.

Source: UN Comtrade (comtradeapi.un.org public preview endpoint, no key) —
US (reporter 842) imports, calendar year 2024, HS6 level. For each line in
cross_rulings_dataset.json we take the real average unit value
(primaryValue / qty) of the matching HS6 commodity, pick a plausible
shipment quantity, and recompute declared_value = qty x real unit value.

Rows whose HS6 has no usable quantity data keep a per-kg price (netWgt)
or, failing that, keep the old synthetic value and are marked estimated.
"""
import json
import math
import random
import time
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).parent
API = "https://comtradeapi.un.org/public/v1/preview/C/A/HS"
CHUNK = 20

UNIT_ABBR = {
    1: None, 5: "units", 6: "pairs", 7: "dozen", 8: "kg", 9: "1000 kWh",
    10: "m", 11: "m2", 12: "m3", 13: "l", 14: "1000 u", 15: "carat",
}


def fetch_chunk(codes):
    qs = (f"?reporterCode=842&period=2024&flowCode=M&partnerCode=0"
          f"&cmdCode={','.join(codes)}")
    req = urllib.request.Request(API + qs, headers={"User-Agent": "TariffCheck-test-data/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r).get("data", [])


def nice_qty(q):
    """Round a raw quantity to something an invoice would actually show."""
    if q >= 1000:
        return int(round(q / 100.0) * 100)
    if q >= 100:
        return int(round(q / 10.0) * 10)
    return max(1, int(round(q)))


def main():
    rows = json.loads((HERE / "cross_rulings_dataset.json").read_text())
    rng = random.Random(2026)

    hs6 = sorted({r["hts_code"].replace(".", "")[:6] for r in rows})
    print(f"{len(rows)} rows, {len(hs6)} unique HS6 commodities to price")

    prices = {}
    skipped_chunks = []
    for i in range(0, len(hs6), CHUNK):
        chunk = hs6[i:i + CHUNK]
        n = i // CHUNK + 1
        data = None
        for attempt in range(3):
            try:
                data = fetch_chunk(chunk)
                break
            except urllib.error.HTTPError as e:
                if e.code == 429:
                    print(f"  ! chunk {n}: 429 rate limited — waiting 60s")
                    time.sleep(60)
                else:
                    print(f"  ! chunk {n}: {e} — retrying in 5s")
                    time.sleep(5)
            except Exception as e:
                print(f"  ! chunk {n}: {e} — retrying in 5s")
                time.sleep(5)
        if data is None:
            print(f"  ! chunk {n}: failed after retries — skipping")
            skipped_chunks.append(n)
            continue
        for rec in data:
            code = rec["cmdCode"]
            val = rec.get("primaryValue") or 0
            qty = rec.get("qty") or 0
            unit = UNIT_ABBR.get(rec.get("qtyUnitCode"))
            wgt = rec.get("netWgt") or 0
            if val > 0 and qty > 0 and unit:
                prices[code] = {"unit_value": val / qty, "unit": unit,
                                "us_imports_2024_usd": val}
            elif val > 0 and wgt > 0:
                prices[code] = {"unit_value": val / wgt, "unit": "kg",
                                "us_imports_2024_usd": val}
        print(f"  chunk {n}: priced {len(prices)}/{len(hs6)}")
        time.sleep(1.2)
    if skipped_chunks:
        print(f"  !! skipped chunks: {skipped_chunks}")

    priced, estimated = 0, 0
    for r in rows:
        code6 = r["hts_code"].replace(".", "")[:6]
        p = prices.get(code6)
        if p:
            uv = p["unit_value"]
            # plausible shipment: aim for a $3k-$70k line at the real unit price
            target = rng.uniform(3000, 70000)
            qty = nice_qty(max(1.0, target / uv))
            unit_price = round(uv, 2 if uv >= 1 else 4)
            r.update(
                qty=qty, qty_unit=p["unit"], unit_price=unit_price,
                declared_value=round(qty * unit_price, 2),
                price_source=f"UN Comtrade, US general imports 2024, HS {code6} "
                             f"(${p['us_imports_2024_usd']:,.0f} total)",
                price_real=True,
            )
            priced += 1
        else:
            r.update(price_real=False,
                     price_source="estimated (no 2024 US import quantity data for HS6)")
            estimated += 1

    (HERE / "cross_rulings_dataset.json").write_text(json.dumps(rows, indent=2))
    print(f"\n{priced} rows priced from real 2024 US import data, {estimated} left estimated")

    # regenerate batch bodies with the new values
    for n, start in enumerate(range(0, len(rows), 100), 1):
        chunk = rows[start:start + 100]
        body = {"rows": [
            {"row_id": r["row_id"], "hts_code": r["hts_code"],
             "description": r["description"],
             "declared_value": r["declared_value"],
             **({"origin": r["origin"]} if r["origin"] else {})}
            for r in chunk
        ]}
        (HERE / f"batch_rows_{n}.json").write_text(json.dumps(body, indent=2))
    print("batch_rows_*.json regenerated")

    sample = [r for r in rows if r.get("price_real")][:5]
    for r in sample:
        print(f'  {r["hts_code"]} {r["description"][:40]:40} '
              f'{r["qty"]:>8,} {r["qty_unit"]:>5} x ${r["unit_price"]:>10,.2f} '
              f'= ${r["declared_value"]:>12,.2f}')


if __name__ == "__main__":
    main()
