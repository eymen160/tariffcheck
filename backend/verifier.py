# TariffCheck deterministic verification layer.
#
# Every AI-generated finding is re-verified against the full official USITC
# HTS 2026 schedule (backend/data/hts_db.json.gz, ~29,755 codes) before it can
# reach the API response or the protest letter. Pure Python, zero API calls:
# the model proposes, this module disposes. A hallucinated code or a wrong
# dollar amount physically cannot survive this pass.

import re

from hts_database import (
    lookup_hts,
    fta_rate_for_code,
    get_section_301,
    HTS_RATES,
)

VERIFICATION_SOURCE = f"USITC HTS 2026 ({len(HTS_RATES):,} codes)"


def _dedup_findings(findings):
    """Drop exact-duplicate findings (same current code, suggested code and
    declared value) — the model occasionally emits the same line twice, which
    would double-count savings in the letter."""
    seen = set()
    out = []
    for f in findings:
        key = (
            str(f.get("hts_code") or ""),
            str(f.get("suggested_code") or ""),
            str(f.get("declared_value") or ""),
        )
        if key in seen:
            continue
        seen.add(key)
        out.append(f)
    return out


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
    if finding.get("code_prefix_matched") and confidence == "high":
        return "medium"
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
    suppressed = 0
    kept = []

    analysis["findings"] = _dedup_findings(analysis.get("findings", []))

    for f in analysis["findings"]:
        f["verified"] = False
        f["verification_note"] = None
        kept.append(f)

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

        s301_cur, s301_cur_est = get_section_301(f.get("hts_code"), origin)
        s301_sug, s301_sug_est = get_section_301(f["suggested_code"], origin)

        # FTA path: if a special program rate applies to the suggested code
        # for this origin, that is the rate the importer would actually pay.
        _fta_name, fta_rate = fta_rate_for_code(f["suggested_code"], origin)

        eff_cur = round(cur_rate + s301_cur, 4)
        eff_sug = round((fta_rate if fta_rate is not None else sug_rate) + s301_sug, 4)
        declared_value = float(f.get("declared_value") or 0)

        # Same-subheading suppression: the model sometimes "suggests" the very
        # code already on the line — truncated, reformatted, or with a shuffled
        # statistical suffix. Rates are set at the 8-digit subheading, so when
        # both codes share it AND the effective rates are identical (Section
        # 301 can differ at 10 digits, so dollars are checked, not assumed)
        # there is nothing to protest and the finding is dropped.
        cur_digits = re.sub(r"\D", "", str(f.get("hts_code") or ""))
        sug_digits = re.sub(r"\D", "", sug["code"])
        if (cur is not None and len(cur_digits) >= 8
                and cur_digits[:8] == sug_digits[:8] and eff_cur == eff_sug):
            suppressed += 1
            kept.pop()
            continue
        official_savings = round(max(0.0, (eff_cur - eff_sug) / 100.0) * declared_value, 2)

        # Overwrite the model's arithmetic with ours; record the delta.
        try:
            model_savings = float(f.get("savings") or 0)
        except (TypeError, ValueError):
            model_savings = 0.0
        if abs(official_savings - model_savings) > 1.0:
            f["model_claimed_savings"] = model_savings

        # Remedy routing. Dollars that exist only because an unclaimed FTA
        # preference would apply are NOT protestable under 19 U.S.C. §1514 —
        # CBP rejects post-importation preference claims raised via protest;
        # the exclusive vehicle is 19 U.S.C. 1520(d), within ONE YEAR of
        # importation. Pure reclassification deltas remain §1514 material.
        notes = []
        reclass_delta = round((cur_rate + s301_cur) - (sug_rate + s301_sug), 4)
        if official_savings > 0 and fta_rate is not None and reclass_delta <= 0:
            f["remedy"] = "1520d"
            notes.append(
                f"Unclaimed {_fta_name} preference — recoverable via 19 U.S.C. "
                "1520(d) within 1 year of importation (rules-of-origin "
                "qualification and certification required), not a §1514 protest"
            )
        elif official_savings > 0:
            f["remedy"] = "1514"
            if fta_rate is not None and fta_rate < sug_rate:
                notes.append(
                    f"Savings include an unclaimed {_fta_name} preference "
                    "component — FTA qualification (certification of origin) "
                    "required"
                )
        elif eff_sug > eff_cur and declared_value > 0:
            # Two-way audit honesty: the correct code costs MORE. Never hide
            # the downside — this is a prior-disclosure conversation.
            f["remedy"] = None
            notes.append(
                "Correct classification carries a HIGHER rate — possible duty "
                "underpayment. Discuss prior disclosure (19 U.S.C. 1592(c)(4)) "
                "with your broker or counsel before any filing."
            )
        else:
            f["remedy"] = None

        # A suggested code that only resolved via prefix fallback means the
        # model's statistical suffix does not exist in the schedule. Never
        # silently launder it into "verified" at full confidence.
        if str(sug.get("note") or "").startswith("Matched from prefix"):
            f["code_prefix_matched"] = True
            notes.append(
                "Suggested code matched only at prefix level — the statistical "
                "suffix is unconfirmed; verify the full 10-digit code before "
                "filing"
            )

        # Section 301 figures that could not be verified at line level
        # (partial statistical coverage, ambiguous short code, or chapter
        # fallback when the line-level dataset is absent) are estimates —
        # whenever one touches this finding's dollars, say so.
        if (s301_cur_est or s301_sug_est) and (s301_cur or s301_sug or official_savings > 0):
            notes.append(
                "Section 301 figure could not be verified at line level for "
                "this code — confirm the exact Chapter 99 coverage before "
                "relying on it"
            )

        f["verification_note"] = "; ".join(notes) if notes else None

        f["current_rate"] = cur_rate
        f["suggested_rate"] = sug_rate
        f["section_301_rate"] = s301_cur
        f["total_current_rate"] = eff_cur
        f["total_suggested_rate"] = eff_sug
        f["savings"] = official_savings
        f["verified"] = True
        f["confidence"] = calibrate_confidence(f)
        verified_total += official_savings

    analysis["findings"] = kept
    analysis["total_savings"] = round(verified_total, 2)
    analysis["verification"] = {
        "source": VERIFICATION_SOURCE,
        "verified_count": sum(1 for f in kept if f.get("verified")),
        "total_count": len(kept),
        "suppressed_count": suppressed,
    }
    return analysis
