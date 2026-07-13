import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from verifier import verify_findings, calibrate_confidence, VERIFICATION_SOURCE

# Known schedule facts (asserted in test_hts_lookup.py):
#   6109.90.10.90 → 32.0% MFN
#   6109.10.00.12 → 16.5% MFN
#   0102.29.40.24 → '1¢/kg' → general_rate None (unparseable)


def _analysis(**finding_overrides):
    finding = {
        "hts_code": "6109.90.1090",
        "description": "T-shirts",
        "current_rate": 32.0,
        "suggested_code": "6109.10.0012",
        "suggested_rate": 16.5,
        "declared_value": 10000,
        "savings": 1550.0,
        "confidence": "high",
        "explanation": "chief weight cotton",
    }
    finding.update(finding_overrides)
    return {
        "findings": [finding],
        "total_savings": finding.get("savings", 0),
        "country_of_origin": "Bangladesh",
    }


def test_invented_suggested_code_is_unverified_and_zeroed():
    analysis = verify_findings(_analysis(suggested_code="9999.99.9999", savings=500000))
    f = analysis["findings"][0]
    assert f["verified"] is False
    assert f["savings"] == 0
    assert f["verification_note"] == "Suggested code not in USITC 2026 schedule"
    assert f["confidence"] == "low"          # unverified can never be high
    assert analysis["total_savings"] == 0
    assert analysis["verification"]["verified_count"] == 0
    assert analysis["verification"]["total_count"] == 1


def test_unparseable_rate_is_unverified():
    analysis = verify_findings(_analysis(hts_code="0102.29.40.24"))
    f = analysis["findings"][0]
    assert f["verified"] is False
    assert f["verification_note"] == "Rate not machine-parseable — manual review"
    assert f["confidence"] == "low"
    assert analysis["total_savings"] == 0


def test_correct_pair_recomputes_savings_hand_math():
    # (32.0 - 16.5) / 100 * 10000 = 1550.00 — Bangladesh: no 301, no FTA
    analysis = verify_findings(_analysis())
    f = analysis["findings"][0]
    assert f["verified"] is True
    assert f["verification_note"] is None
    assert f["suggested_code"] == "6109.10.00.12"     # canonical dotted form
    assert f["current_rate"] == 32.0
    assert f["suggested_rate"] == 16.5
    assert f["total_current_rate"] == 32.0
    assert f["total_suggested_rate"] == 16.5
    assert f["savings"] == 1550.0
    assert "model_claimed_savings" not in f           # model math agreed
    assert f["confidence"] == "high"                  # rates agreed → model's call stands
    assert analysis["total_savings"] == 1550.0
    assert analysis["verification"] == {
        "source": VERIFICATION_SOURCE,
        "verified_count": 1,
        "total_count": 1,
        "suppressed_count": 0,
    }


def test_wrong_model_math_is_overwritten_and_recorded():
    analysis = verify_findings(_analysis(savings=8100.0))
    f = analysis["findings"][0]
    assert f["verified"] is True
    assert f["savings"] == 1550.0                     # server recompute wins
    assert f["model_claimed_savings"] == 8100.0
    assert f["confidence"] == "medium"                # wrong math caps at medium
    assert analysis["total_savings"] == 1550.0


def test_section_301_stacking_in_effective_rates():
    # Line-level USITC China Tariffs data (backend/data/section301.json):
    # 9403.60.80 furniture is List 3 (25%), so a China reclass INTO covered
    # furniture must stack +25 on the suggested side and kill the "savings".
    analysis = verify_findings({
        "findings": [{
            "hts_code": "9617.00.9000",      # 7.2% MFN, NOT 301-covered
            "suggested_code": "9403.60.8080",  # 0% MFN + 25% List 3
            "declared_value": 10000,
            "savings": 720,
            "confidence": "high",
        }],
        "total_savings": 720,
        "country_of_origin": "China",
    })
    f = analysis["findings"][0]
    assert f["verified"] is True
    assert f["total_current_rate"] == 7.2
    assert f["total_suggested_rate"] == 25.0
    assert f["savings"] == 0.0
    assert f["model_claimed_savings"] == 720


def test_suspended_list_4b_codes_carry_no_301():
    # 7323.93 sits on suspended List 4B — the old chapter table wrongly
    # charged it 25%. The tumbler reclass (9617 7.2% → 7323.93 2%, no 301)
    # is therefore a REAL $377 recovery, verified at line level.
    analysis = verify_findings({
        "findings": [{
            "hts_code": "9617.00.9000",
            "suggested_code": "7323.93.0060",
            "declared_value": 7250,
            "savings": 377,
            "confidence": "high",
        }],
        "total_savings": 377,
        "country_of_origin": "China",
    })
    f = analysis["findings"][0]
    assert f["verified"] is True
    assert f["total_suggested_rate"] == 2.0
    assert f["savings"] == 377.0
    assert f["remedy"] == "1514"


def test_duplicate_findings_are_deduped():
    # The model occasionally emits the same line twice — savings must not
    # double-count (live bug: $5,504 demanded on a $2,752 finding).
    finding = {
        "hts_code": "6109.90.1090",
        "suggested_code": "6109.10.0012",
        "declared_value": 10000,
        "savings": 1550.0,
        "confidence": "high",
    }
    analysis = verify_findings({
        "findings": [dict(finding), dict(finding)],
        "total_savings": 3100,
        "country_of_origin": "Bangladesh",
    })
    assert len(analysis["findings"]) == 1
    assert analysis["total_savings"] == 1550.0


def test_unclaimed_fta_routes_to_1520d_not_1514():
    # Pure FTA recovery (same code, preference unclaimed) is not protestable
    # under §1514 — the exclusive vehicle is 19 U.S.C. 1520(d).
    analysis = verify_findings({
        "findings": [{
            "hts_code": "8708.99.8180",
            "suggested_code": "8708.99.8180",
            "declared_value": 43500,
            "savings": 1088,
            "confidence": "high",
        }],
        "total_savings": 1088,
        "country_of_origin": "South Korea",
    })
    f = analysis["findings"][0]
    assert f["verified"] is True
    assert f["savings"] == 1087.5
    assert f["remedy"] == "1520d"
    assert "1520(d)" in f["verification_note"]


def test_higher_correct_rate_flags_possible_underpayment():
    # Two-way audit: when the correct code costs MORE, never hide it —
    # surface the prior-disclosure conversation. (Cotton tee wrongly entered
    # under the cotton code when the goods are chief-weight synthetic.)
    analysis = verify_findings({
        "findings": [{
            "hts_code": "6109.10.0012",       # 16.5%
            "suggested_code": "6109.90.1090",  # 32%
            "declared_value": 10000,
            "savings": 0,
            "confidence": "high",
        }],
        "total_savings": 0,
        "country_of_origin": "Bangladesh",
    })
    f = analysis["findings"][0]
    assert f["savings"] == 0.0
    assert f["remedy"] is None
    assert "underpayment" in f["verification_note"]
    assert "1592(c)(4)" in f["verification_note"]


def test_iso_country_codes_trigger_section_301_and_fta():
    # ACE exports carry ISO codes; "CN" must behave exactly like "China"
    # (the old substring matching silently returned 0% 301 / no FTA).
    from hts_database import normalize_country, check_fta, get_section_301
    assert normalize_country("CN") == "china"
    assert normalize_country("Made in China") == "china"
    assert normalize_country("MX") == "mexico"
    assert normalize_country("Türkiye") == "turkey"
    assert get_section_301("9403.60.8040", "CN")[0] == get_section_301("9403.60.8040", "China")[0] > 0
    assert check_fta("KR")[0] == "KORUS"


def test_north_korea_does_not_qualify_for_korus():
    from hts_database import check_fta, normalize_country
    assert normalize_country("North Korea") == "north korea"
    assert check_fta("North Korea") == (None, None, None)
    assert check_fta("Democratic People's Republic of Korea") == (None, None, None)


def test_prefix_fallback_suggested_code_is_flagged_and_capped():
    # An invented statistical suffix must never launder into full-confidence
    # "verified" via prefix fallback.
    analysis = verify_findings({
        "findings": [{
            "hts_code": "6109.90.1090",
            "suggested_code": "6109.10.0999",   # does not exist; prefix-matches a neighbor
            "declared_value": 10000,
            "savings": 1550,
            "confidence": "high",
        }],
        "total_savings": 1550,
        "country_of_origin": "Bangladesh",
    })
    f = analysis["findings"][0]
    assert f["verified"] is True
    assert f["code_prefix_matched"] is True
    assert f["confidence"] == "medium"
    assert "prefix level" in f["verification_note"]


def test_calibrate_confidence_clamps():
    assert calibrate_confidence({"verified": False, "confidence": "high"}) == "low"
    assert calibrate_confidence({"verified": True, "confidence": "high",
                                 "model_claimed_savings": 5.0}) == "medium"
    assert calibrate_confidence({"verified": True, "confidence": "low",
                                 "model_claimed_savings": 5.0}) == "low"
    assert calibrate_confidence({"verified": True, "confidence": "high"}) == "high"
    assert calibrate_confidence({"verified": True}) == "medium"   # missing → medium


def test_same_code_reformatted_is_suppressed():
    # Model "suggests" the parent of the very code on the line (3004.39.0055 →
    # 3004.39.00) — not a reclassification, just the same subheading truncated.
    analysis = verify_findings(_analysis(
        hts_code="3004.39.0055", suggested_code="3004.39.00",
        current_rate=0.0, suggested_rate=0.0, savings=0,
    ))
    assert analysis["findings"] == []
    assert analysis["verification"]["total_count"] == 0
    assert analysis["verification"]["suppressed_count"] == 1
    assert analysis["total_savings"] == 0


def test_statistical_suffix_change_same_rate_is_suppressed():
    # 8479.89.9599 → 8479.89.9595: same 8-digit subheading, same 2.5% rate —
    # a statistical-suffix shuffle with zero duty impact must not surface.
    analysis = verify_findings(_analysis(
        hts_code="8479.89.9599", suggested_code="8479.89.9595",
        current_rate=2.5, suggested_rate=2.5, savings=0,
    ))
    analysis["country_of_origin"] = "Italy"
    assert analysis["findings"] == []
    assert analysis["verification"]["suppressed_count"] == 1


def test_real_reclassification_not_suppressed():
    # The canonical cotton t-shirt reclass (6109.90 → 6109.10) crosses
    # subheadings and must keep flowing through untouched.
    analysis = verify_findings(_analysis())
    assert len(analysis["findings"]) == 1
    assert analysis["verification"]["suppressed_count"] == 0
    assert analysis["findings"][0]["verified"] is True
