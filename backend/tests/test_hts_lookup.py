import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hts_database import lookup_hts


def test_exact_lookup_returns_canonical_dotted_code():
    rec = lookup_hts("9403.40.9060")
    assert rec is not None
    assert rec["code"] == "9403.40.90.60"
    assert rec["general_rate"] == 0.0
    assert "note" not in rec


def test_exact_lookup_known_rates():
    assert lookup_hts("6109.90.1090")["general_rate"] == 32.0
    assert lookup_hts("6109.10.0012")["general_rate"] == 16.5
    # Unparseable specific duty stays None with the raw string preserved
    rec = lookup_hts("0102.29.40.24")
    assert rec.get("general_rate") is None   # key absent when unparseable
    assert rec["general_raw"]


def test_lookup_accepts_bare_digits():
    assert lookup_hts("9403409060")["code"] == "9403.40.90.60"


def test_prefix_fallback_surfaces_note():
    rec = lookup_hts("9403.40")
    assert rec is not None
    assert rec["code"].startswith("9403.40")
    assert "note" in rec and rec["note"]


def test_unknown_code_returns_none():
    assert lookup_hts("9999.99.9999") is None
    assert lookup_hts("") is None
    assert lookup_hts(None) is None
