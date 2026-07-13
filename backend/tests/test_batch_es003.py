"""ACE ES-003 fields on the batch endpoint: SPI suppression, real protest
windows, duty_paid-based savings, and the unquantified-rate honesty fix."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from batch_audit import run_batch_audit


def _row(**kw):
    base = {"row_id": 1, "hts_code": "6109.10.0012", "description": "cotton t-shirts",
            "declared_value": 10000, "origin": "MX"}
    base.update(kw)
    return base


def test_spi_claimed_suppresses_missed_fta():
    # Mexico cotton t-shirts at 16.5% MFN would normally flag missed USMCA;
    # when the broker already claimed it (SPI 'S'), accusing them is a false
    # positive that kills a pilot.
    without_spi = run_batch_audit({"rows": [_row()]})["results"][0]
    with_spi = run_batch_audit({"rows": [_row(spi_claimed="S")]})["results"][0]
    assert without_spi["issue"] == "missed_fta"
    assert with_spi["issue"] is None
    assert with_spi["status"] == "ok"


def test_missed_fta_note_routes_to_1520d_not_protest():
    r = run_batch_audit({"rows": [_row()]})["results"][0]
    assert "1520(d)" in r["note"]
    assert "protest" not in r["note"].split("1520(d)")[0].lower() or "NOT a §1514" in r["note"]


def test_iso_origin_codes_work_in_batch():
    # "MX" must behave like "Mexico" (the old substring matching silently
    # produced no FTA flag for ISO codes).
    iso = run_batch_audit({"rows": [_row(origin="MX")]})["results"][0]
    name = run_batch_audit({"rows": [_row(origin="Mexico")]})["results"][0]
    assert iso["issue"] == name["issue"] == "missed_fta"
    assert iso["origin_normalized"] == "mexico"


def test_protest_window_computed_from_liquidation_date():
    r = run_batch_audit({"rows": [_row(
        entry_no="ATL-123", entry_date="2025-09-01",
        liquidation_date="2026-06-01",
    )]})["results"][0]
    assert r["entry_no"] == "ATL-123"
    assert r["liquidation_status"] == "liquidated"
    assert r["protest_by"] == "2026-11-28"
    assert r["remedy_vehicle"] == "1514"


def test_unliquidated_rows_route_to_psc():
    r = run_batch_audit({"rows": [_row(liquidation_status="not_liquidated")]})["results"][0]
    assert r["remedy_vehicle"] == "psc"
    assert r["protest_by"] is None


def test_duty_paid_beats_schedule_delta():
    # duty_paid $2,000 on a line whose corrected duty is 0% → savings = $2,000
    r = run_batch_audit({"rows": [_row(duty_paid=2000)]})["results"][0]
    assert r["issue"] == "missed_fta"
    assert r["estimated_savings"] == 2000.0


def test_specific_duty_rows_are_no_longer_silently_confident():
    # 0805.50.2050 (lemons, cents/kg) has no parseable ad-valorem rate; the
    # old behavior returned confidence 'high' with no note (tester bug #4).
    r = run_batch_audit({"rows": [{
        "row_id": 1, "hts_code": "0805.50.2050", "declared_value": 1000,
        "origin": "Mexico",
    }]})["results"][0]
    assert r["current_rate"] is None
    assert r["confidence"] == "low"
    assert "NOT quantified" in r["note"]
