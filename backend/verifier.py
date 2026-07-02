# TariffCheck deterministic verification layer.
#
# Every AI-generated finding is re-verified against the full official USITC
# HTS 2026 schedule (backend/data/hts_db.json.gz, ~29,755 codes) before it can
# reach the API response or the protest letter. Pure Python, zero API calls:
# the model proposes, this module disposes. A hallucinated code or a wrong
# dollar amount physically cannot survive this pass.

from hts_database import (
    lookup_hts,
    fta_rate_for_code,
    get_section_301_rate,
    HTS_RATES,
)

VERIFICATION_SOURCE = f"USITC HTS 2026 ({len(HTS_RATES):,} codes)"


def calibrate_confidence(finding):
    """Deterministic confidence clamp — self-reported confidence has
    server-side consequences:
      - an unverified finding can never be better than "low";
      - a finding whose arithmetic we had to overwrite caps at "medium"."""
    confidence = finding.get("confidence") or "medium"
    if confidence not in ("high", "medium", "low"):
        confidence = "medium"
    if not finding.get("verified"):
        return "low"
    if finding.get("model_claimed_savings") is not None and confidence == "high":
        return "medium"
    return confidence


def verify_findings(analysis, origin_hint=None):
    """Recompute every finding against HTS_RATES. Mutates and returns
    `analysis`. Sets per-finding `verified`, `verification_note`,
    `model_claimed_savings` (only when the model's math was wrong by > $1),
    canonicalizes `suggested_code`, overwrites all rates/savings with official
    figures, and replaces `total_savings` with the verified sum."""
    origin = analysis.get("country_of_origin") or origin_hint or ""
    verified_total = 0.0

    for f in analysis.get("findings", []):
        f["verified"] = False
        f["verification_note"] = None

        cur = lookup_hts(f.get("hts_code"))
        sug = lookup_hts(f.get("suggested_code"))

        if sug is None:
            # Model invented a code — hard flag, zero the savings.
            f["verification_note"] = "Suggested code not in USITC 2026 schedule"
            f["savings"] = 0
            f["confidence"] = calibrate_confidence(f)
            continue

        f["suggested_code"] = sug["code"]  # canonical dotted form

        cur_rate = cur.get("general_rate") if cur else None
        sug_rate = sug.get("general_rate")
        if cur_rate is None or sug_rate is None:
            f["verification_note"] = "Rate not machine-parseable — manual review"
            f["confidence"] = calibrate_confidence(f)
            continue

        s301_cur = get_section_301_rate(f.get("hts_code"), origin)
        s301_sug = get_section_301_rate(f["suggested_code"], origin)

        # FTA path: if a special program rate applies to the suggested code
        # for this origin, that is the rate the importer would actually pay.
        _fta_name, fta_rate = fta_rate_for_code(f["suggested_code"], origin)

        eff_cur = round(cur_rate + s301_cur, 4)
        eff_sug = round((fta_rate if fta_rate is not None else sug_rate) + s301_sug, 4)
        declared_value = float(f.get("declared_value") or 0)
        official_savings = round(max(0.0, (eff_cur - eff_sug) / 100.0) * declared_value, 2)

        # Overwrite the model's arithmetic with ours; record the delta.
        try:
            model_savings = float(f.get("savings") or 0)
        except (TypeError, ValueError):
            model_savings = 0.0
        if abs(official_savings - model_savings) > 1.0:
            f["model_claimed_savings"] = model_savings

        f["current_rate"] = cur_rate
        f["suggested_rate"] = sug_rate
        f["section_301_rate"] = s301_cur
        f["total_current_rate"] = eff_cur
        f["total_suggested_rate"] = eff_sug
        f["savings"] = official_savings
        f["verified"] = True
        f["confidence"] = calibrate_confidence(f)
        verified_total += official_savings

    findings = analysis.get("findings", [])
    analysis["total_savings"] = round(verified_total, 2)
    analysis["verification"] = {
        "source": VERIFICATION_SOURCE,
        "verified_count": sum(1 for f in findings if f.get("verified")),
        "total_count": len(findings),
    }
    return analysis
