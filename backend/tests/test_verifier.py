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
    # China tumbler demo economics: 9617 (7.2%, no 301) → 7323.93 (2% + 25% 301)
    # is NOT a savings — eff 7.2 vs 27.0 → savings must be zero.
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
    assert f["total_current_rate"] == 7.2
    assert f["total_suggested_rate"] == 27.0
    assert f["savings"] == 0.0
    assert f["model_claimed_savings"] == 377


def test_calibrate_confidence_clamps():
    assert calibrate_confidence({"verified": False, "confidence": "high"}) == "low"
    assert calibrate_confidence({"verified": True, "confidence": "high",
                                 "model_claimed_savings": 5.0}) == "medium"
    assert calibrate_confidence({"verified": True, "confidence": "low",
                                 "model_claimed_savings": 5.0}) == "low"
    assert calibrate_confidence({"verified": True, "confidence": "high"}) == "high"
    assert calibrate_confidence({"verified": True}) == "medium"   # missing → medium
