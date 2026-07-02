# TariffCheck batch audit — the broker feature.
#
# Fully deterministic screen of entry lines against the official USITC HTS
# 2026 schedule plus the curated misclassification patterns and FTA/Section
# 301 overlays in hts_database.py. Zero Claude calls: runs with no API key,
# fast enough for 100-row requests well under a second.

import re

from hts_database import (
    lookup_hts,
    fta_rate_for_code,
    check_fta,
    get_misclassification_hints,
    get_section_301_rate,
)
from verifier import VERIFICATION_SOURCE

MAX_BATCH_ROWS = 100

BATCH_DISCLAIMER = (
    "Deterministic screen against the official schedule and curated "
    "misclassification patterns. Findings must be reviewed by a licensed "
    "customs broker or the importer of record before filing."
)

# hts_code must be digits/dots resolving to 4-10 digits
_HTS_INPUT_RE = re.compile(r"^[\d.]+$")


class BatchValidationError(Exception):
    """Raised for request-level validation failures (whole request → 400)."""

    def __init__(self, code, message):
        super().__init__(message)
        self.code = code
        self.message = message


def _parse_value(raw):
    """Return declared_value as float, or None when absent/unusable."""
    if raw is None or raw == "":
        return None
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return None
    return value if value > 0 else None


def _error_row(row_id, description, declared_value, origin, note):
    return {
        "row_id": row_id,
        "status": "error",
        "current_code": None,
        "current_code_found": False,
        "description": description,
        "declared_value": declared_value,
        "origin": origin,
        "current_rate": None,
        "section_301_rate": None,
        "total_current_rate": None,
        "issue": None,
        "suggested_code": None,
        "suggested_rate": None,
        "total_suggested_rate": None,
        "estimated_savings": 0,
        "confidence": "low",
        "verified": False,
        "note": note,
    }


def audit_row(row, index):
    """Audit a single entry line. `index` is the 1-based position, used for
    error messages when the row carries no row_id."""
    if not isinstance(row, dict):
        raise BatchValidationError("invalid_row", f"Row {index}: must be an object.")

    row_id = row.get("row_id", index)
    raw_code = str(row.get("hts_code") or "").strip()
    description = str(row.get("description") or "").strip() or None
    origin = str(row.get("origin") or "").strip() or None
    declared_value = _parse_value(row.get("declared_value"))

    if not raw_code:
        raise BatchValidationError("invalid_row", f"Row {row_id}: hts_code is required.")

    digits = re.sub(r"\D", "", raw_code)
    if not _HTS_INPUT_RE.match(raw_code) or not (4 <= len(digits) <= 10):
        return _error_row(
            row_id, description, declared_value, origin,
            f"hts_code '{raw_code}' is not a valid HTS code (expect 4-10 digits, dots allowed).",
        )

    rec = lookup_hts(digits)
    if rec is None:
        return {
            "row_id": row_id,
            "status": "flagged",
            "current_code": raw_code,
            "current_code_found": False,
            "description": description,
            "declared_value": declared_value,
            "origin": origin,
            "current_rate": None,
            "section_301_rate": get_section_301_rate(digits, origin),
            "total_current_rate": None,
            "issue": "code_not_found",
            "suggested_code": None,
            "suggested_rate": None,
            "total_suggested_rate": None,
            "estimated_savings": 0,
            "confidence": "low",
            "verified": True,
            "note": "HTS code not found in the USITC 2026 schedule — entry may be rejected or misfiled.",
        }

    current_code = rec["code"]
    current_rate = rec.get("general_rate")  # None when 'Free'-style raw was unparseable
    s301 = get_section_301_rate(digits, origin)
    total_current = round(current_rate + s301, 4) if current_rate is not None else None

    result = {
        "row_id": row_id,
        "status": "ok",
        "current_code": current_code,
        "current_code_found": True,
        "description": description,
        "declared_value": declared_value,
        "origin": origin,
        "current_rate": current_rate,
        "section_301_rate": s301,
        "total_current_rate": total_current,
        "issue": None,
        "suggested_code": None,
        "suggested_rate": None,
        "total_suggested_rate": None,
        "estimated_savings": 0,
        "confidence": "high",
        "verified": True,
        "note": None,
    }

    # 1) Curated misclassification patterns (description-keyed).
    for hint in get_misclassification_hints(current_code, description or ""):
        suggested = lookup_hts(hint["suggest"])
        if suggested is None or suggested.get("general_rate") is None:
            continue
        sug_rate = suggested["general_rate"]
        sug_s301 = get_section_301_rate(suggested["code"], origin)
        total_suggested = round(sug_rate + sug_s301, 4)
        savings = 0
        if declared_value is not None and total_current is not None:
            savings = round(max(0.0, (total_current - total_suggested) / 100.0) * declared_value, 2)
        result.update(
            status="flagged",
            issue="possible_misclassification",
            suggested_code=suggested["code"],
            suggested_rate=sug_rate,
            total_suggested_rate=total_suggested,
            estimated_savings=savings,
            confidence="medium",
            note=f"Matches curated misclassification pattern: {hint['reason']}",
        )
        return result

    # 2) Missed FTA: the origin qualifies for a program with a lower rate
    #    than the effective paid rate on this exact code.
    if origin and current_rate is not None and current_rate > 0:
        fta_name, fta_rate = fta_rate_for_code(current_code, origin)
        if fta_rate is None:
            country_name, country_rate, _form = check_fta(origin)
            if country_name is not None:
                fta_name, fta_rate = country_name, country_rate
        if fta_rate is not None and fta_rate < current_rate:
            total_suggested = round(fta_rate + s301, 4)
            savings = 0
            if declared_value is not None:
                savings = round(max(0.0, (total_current - total_suggested) / 100.0) * declared_value, 2)
            result.update(
                status="flagged",
                issue="missed_fta",
                suggested_code=current_code,
                suggested_rate=fta_rate,
                total_suggested_rate=total_suggested,
                estimated_savings=savings,
                confidence="high",
                note=f"Origin qualifies for {fta_name} preferential rate "
                     f"({fta_rate}% vs {current_rate}% MFN) — claim the program on entry or protest.",
            )
            return result

    return result


def run_batch_audit(payload):
    """Validate and audit a batch request body. Returns the response dict.
    Raises BatchValidationError for request-level 400s."""
    if not isinstance(payload, dict):
        raise BatchValidationError("no_rows", "Provide 1-100 rows.")
    rows = payload.get("rows")
    if not isinstance(rows, list) or len(rows) == 0:
        raise BatchValidationError("no_rows", "Provide 1-100 rows.")
    if len(rows) > MAX_BATCH_ROWS:
        raise BatchValidationError("too_many_rows", "Maximum 100 rows per request — send in chunks.")

    results = [audit_row(row, i) for i, row in enumerate(rows, start=1)]
    flagged = sum(1 for r in results if r["status"] == "flagged")
    exposure = round(sum(r["estimated_savings"] or 0 for r in results), 2)

    return {
        "summary": {
            "rows": len(results),
            "flagged": flagged,
            "total_estimated_exposure": exposure,
            "source": VERIFICATION_SOURCE,
            "disclaimer": BATCH_DISCLAIMER,
        },
        "results": results,
    }
