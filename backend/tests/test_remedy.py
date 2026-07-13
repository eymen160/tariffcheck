import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from remedy import build_remedy_summary, parse_date, protest_window
from app import generate_protest_letter

TODAY = date(2026, 7, 13)

FINDING = {
    "hts_code": "6109.90.1090", "suggested_code": "6109.10.00.12",
    "declared_value": 10000, "savings": 1550.0, "verified": True,
    "remedy": "1514", "confidence": "high",
}


def test_parse_date_formats():
    assert parse_date("2026-03-04") == date(2026, 3, 4)
    assert parse_date("03/04/2026") == date(2026, 3, 4)
    assert parse_date("") is None
    assert parse_date("garbage") is None


def test_liquidated_entry_routes_to_1514_with_real_deadline():
    s = build_remedy_summary(entry_date="2025-09-01",
                             liquidation_date="2026-06-01",
                             liquidation_status="liquidated", today=TODAY)
    assert s["classification_vehicle"] == "1514"
    assert s["deadlines"]["protest_1514"] == "2026-11-28"  # liq + 180 days
    assert s["deadlines"]["psc"] is None                    # PSC dead post-liquidation
    assert s["deadlines"]["fta_1520d"] == "2026-09-01"      # entry + 1 year


def test_expired_protest_window_is_flagged_not_hidden():
    s = build_remedy_summary(liquidation_date="2025-06-01",
                             liquidation_status="liquidated", today=TODAY)
    assert s["classification_vehicle"] == "1514_expired"
    letter = generate_protest_letter([dict(FINDING)], 1550.0, remedy_summary=s)
    assert "PROTEST WINDOW APPEARS CLOSED" in letter
    assert "not for filing" in letter


def test_unliquidated_entry_routes_to_psc():
    s = build_remedy_summary(entry_date="2026-03-01",
                             liquidation_status="not_liquidated", today=TODAY)
    assert s["classification_vehicle"] == "psc"
    assert s["deadlines"]["psc"] == "2026-12-26"  # entry + 300 days
    letter = generate_protest_letter([dict(FINDING)], 1550.0, remedy_summary=s)
    assert "Post Summary Correction" in letter
    assert "19 U.S.C. 1501" in letter
    assert "would be premature" in letter
    assert "$1,550.00" in letter


def test_unknown_status_letter_carries_the_liquidation_caveat():
    s = build_remedy_summary(today=TODAY)
    assert s["classification_vehicle"] == "unknown"
    letter = generate_protest_letter([dict(FINDING)], 1550.0, remedy_summary=s)
    assert "Confirm this entry has liquidated before filing" in letter


def test_no_summary_keeps_legacy_1514_letter():
    # Demo letters are generated without entry facts and must stay stable.
    letter = generate_protest_letter([dict(FINDING)], 1550.0)
    assert "Pursuant to 19 U.S.C. §1514(a)(2)" in letter
    assert "Confirm this entry has liquidated" not in letter


def test_protest_window_helper():
    by, days_left, is_open = protest_window("2026-06-01", today=TODAY)
    assert by == "2026-11-28" and is_open and days_left > 0
    by2, days2, open2 = protest_window("2025-06-01", today=TODAY)
    assert open2 is False
    assert protest_window(None) == (None, None, None)
