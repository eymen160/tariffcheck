"""HS 2028 readiness check — will a code survive the Jan 1, 2028 renumbering?

The WCO's HS 2028 amendments re-map ~8% of international subheadings; the
correlation source of record is WCO Table II (HS2022 → HS2028, April 2026,
incl. the July 2026 corrigendum), parsed into data/hs2028_correlations.json.gz
by test_data/build_hs2028_table.py.

Scope honesty (surfaces in every response):
- Correlations exist at the INTERNATIONAL 6-digit level. US 10-digit HTS
  lines for 2028 do not exist yet — USITC publishes the implementing
  schedule in late 2027. A 6-digit "renumbered" verdict means the importer's
  10-digit code WILL change; the final digits are not knowable today.
- A subheading absent from Table II is unchanged at the 6-digit level in
  HS 2028 (its US statistical suffixes may still move — flagged in the note).
"""
import gzip
import json
import re
from pathlib import Path

_DB_PATH = Path(__file__).parent / "data" / "hs2028_correlations.json.gz"

with gzip.open(_DB_PATH, "rt") as _f:
    CORRELATIONS = json.load(_f)

EFFECTIVE = "2028-01-01"
SOURCE = ("WCO Correlation Table II (HS2022→HS2028), April 2026, "
          "incl. July 2026 corrigendum")


def _six_digit(code):
    digits = re.sub(r"\D", "", str(code or ""))
    if len(digits) < 6:
        return None
    return f"{digits[:4]}.{digits[4:6]}"


def check_code(code):
    """Readiness verdict for one code (6/8/10-digit accepted)."""
    sub = _six_digit(code)
    if sub is None:
        return {"code": str(code), "status": "invalid",
                "message": "Provide at least a 6-digit HS/HTS code."}
    entry = CORRELATIONS.get(sub)
    base = {"code": str(code), "subheading_2022": sub,
            "effective": EFFECTIVE, "source": SOURCE}
    if entry is None:
        return {**base, "status": "unchanged",
                "message": ("No HS 2028 transfer at the 6-digit level. US "
                            "statistical suffixes may still be renumbered "
                            "when USITC publishes the 2028 schedule (late "
                            "2027).")}
    targets = entry["targets"]
    if len(targets) == 1:
        status = "renumbered"
        message = (f"Goods of {sub} transfer to {targets[0]['code']} in "
                   "HS 2028. Update classifications before Jan 1, 2028.")
    else:
        status = "split"
        message = (f"{sub} splits across {len(targets)} HS 2028 "
                   "subheadings — a blind one-to-one crosswalk WILL "
                   "misclassify part of these goods. Product-level review "
                   "needed before Jan 1, 2028.")
    return {**base, "status": status, "targets": targets, "message": message}


def check_codes(codes):
    """Batch verdicts + summary for up to 500 codes."""
    results = [check_code(c) for c in codes]
    counts = {}
    for r in results:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    return {
        "results": results,
        "summary": {
            "codes": len(results),
            **{k: counts.get(k, 0)
               for k in ("unchanged", "renumbered", "split", "invalid")},
            "action_needed": counts.get("renumbered", 0) + counts.get("split", 0),
            "effective": EFFECTIVE,
            "source": SOURCE,
        },
    }
