"""Demo integrity: every demo's advertised numbers and protest letter must be
exactly what the deterministic verifier produces — a demo letter can never
claim a figure the verification block refutes, and no letter may assert
agency before CBP."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import MOCK_DEMOS, generate_protest_letter


def test_demo_totals_equal_verified_sums():
    for demo_id, demo in MOCK_DEMOS.items():
        verified_sum = round(
            sum(f.get("savings", 0) for f in demo["findings"] if f.get("verified")), 2
        )
        assert demo["total_savings"] == verified_sum, (
            f"demo {demo_id}: advertised {demo['total_savings']} != verified {verified_sum}"
        )


def test_demo_letters_are_regenerated_from_verified_findings():
    for demo_id, demo in MOCK_DEMOS.items():
        expected = generate_protest_letter(
            demo["findings"], demo["total_savings"], demo.get("fta_type")
        )
        assert demo["protest_letter"] == expected, (
            f"demo {demo_id}: letter drifted from verified findings"
        )


def test_no_agency_signature_anywhere():
    for demo_id, demo in MOCK_DEMOS.items():
        assert "Authorized Importer Representative" not in demo["protest_letter"], (
            f"demo {demo_id}: letter asserts agency before CBP"
        )


def test_fta_recoveries_never_demanded_under_1514():
    # Unclaimed-FTA dollars (remedy 1520d) must not appear inside the §1514
    # demand; they may only appear in the 1520(d) advisory block.
    for demo_id, demo in MOCK_DEMOS.items():
        fta_findings = [f for f in demo["findings"] if f.get("remedy") == "1520d"]
        if not fta_findings:
            continue
        letter = demo["protest_letter"]
        assert "1520(d)" in letter, f"demo {demo_id}: FTA finding without 1520(d) routing"
        protest_section = letter.split("UNCLAIMED FTA PREFERENCES")[0]
        for f in fta_findings:
            assert f"HTS {f.get('hts_code')} →" not in protest_section, (
                f"demo {demo_id}: FTA recovery demanded under §1514"
            )
