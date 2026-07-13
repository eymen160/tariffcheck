"""Remedy routing v2 — which legal vehicle fits, with real statutory clocks.

The three post-entry vehicles and their deadlines are NOT interchangeable:

- ACE Post Summary Correction (PSC): pre-liquidation corrections only —
  filed within 300 days of the entry date AND at least 15 days before the
  scheduled liquidation date (19 U.S.C. 1501; CBP PSC guidance).
- 19 U.S.C. §1514 protest: post-liquidation only — 180 days FROM THE DATE OF
  LIQUIDATION (not entry, not audit). A protest filed before liquidation is
  invalid.
- 19 U.S.C. 1520(d): unclaimed FTA preference (USMCA/KORUS/CTPA...) — one
  year FROM THE DATE OF IMPORTATION. CBP rejects these when raised via §1514.

Callers pass whatever entry facts they have; everything here degrades
honestly — a missing date produces an explanatory note, never a fabricated
deadline.
"""
from datetime import date, datetime, timedelta

PSC_ENTRY_WINDOW_DAYS = 300
PSC_PRE_LIQUIDATION_BUFFER_DAYS = 15
PROTEST_WINDOW_DAYS = 180
FTA_1520D_WINDOW_DAYS = 365


def parse_date(value):
    """Tolerant ISO-ish date parsing ('2026-03-04', '2026/03/04',
    '03/04/2026'). Returns datetime.date or None."""
    s = str(value or "").strip()
    if not s:
        return None
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%m/%d/%Y", "%m-%d-%Y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def normalize_liquidation_status(value):
    s = str(value or "").strip().lower().replace("-", "_").replace(" ", "_")
    if s in ("liquidated", "liq", "yes"):
        return "liquidated"
    if s in ("not_liquidated", "unliquidated", "no", "open", "pending"):
        return "not_liquidated"
    return "unknown"


def build_remedy_summary(entry_date=None, liquidation_date=None,
                         liquidation_status=None, today=None):
    """Compute per-entry deadlines and the correct classification vehicle.

    Returns a JSON-safe dict:
      {
        "liquidation_status": ...,
        "classification_vehicle": "psc" | "1514" | "1514_expired" | "unknown",
        "deadlines": {"psc": iso|None, "protest_1514": iso|None,
                      "fta_1520d": iso|None},
        "notes": [str, ...],
      }
    """
    today = today or date.today()
    e_date = parse_date(entry_date)
    l_date = parse_date(liquidation_date)
    status = normalize_liquidation_status(liquidation_status)
    if status == "unknown" and l_date is not None:
        status = "liquidated"

    deadlines = {"psc": None, "protest_1514": None, "fta_1520d": None}
    notes = []

    if e_date:
        deadlines["fta_1520d"] = (e_date + timedelta(days=FTA_1520D_WINDOW_DAYS)).isoformat()
        deadlines["psc"] = (e_date + timedelta(days=PSC_ENTRY_WINDOW_DAYS)).isoformat()

    if status == "liquidated":
        vehicle = "1514"
        deadlines["psc"] = None  # PSC is off the table after liquidation
        if l_date:
            protest_by = l_date + timedelta(days=PROTEST_WINDOW_DAYS)
            deadlines["protest_1514"] = protest_by.isoformat()
            if today > protest_by:
                vehicle = "1514_expired"
                notes.append(
                    f"The 180-day protest window from liquidation "
                    f"({l_date.isoformat()}) appears to have closed on "
                    f"{protest_by.isoformat()}. Confirm the liquidation date "
                    "on the ACE courtesy notice before abandoning the claim."
                )
        else:
            notes.append(
                "Entry reported as liquidated but no liquidation date was "
                "provided — the §1514 protest deadline is 180 days from the "
                "date of liquidation. Pull it from ACE before filing."
            )
    elif status == "not_liquidated":
        vehicle = "psc"
        notes.append(
            "Entry not yet liquidated — classification corrections go in as "
            "an ACE Post Summary Correction (within 300 days of entry and at "
            "least 15 days before scheduled liquidation), not a §1514 protest."
        )
    else:
        vehicle = "unknown"
        notes.append(
            "Liquidation status not provided. Entries typically liquidate "
            "~314 days after entry: if unliquidated, file a PSC; once "
            "liquidated, a §1514 protest within 180 days of the liquidation "
            "date. Check the entry's status in ACE (or ask your broker) "
            "before filing anything."
        )

    if not e_date:
        notes.append(
            "No entry date provided — the 19 U.S.C. 1520(d) window for "
            "unclaimed FTA preferences is ONE YEAR from the date of "
            "importation; confirm it before relying on an FTA recovery."
        )

    return {
        "liquidation_status": status,
        "classification_vehicle": vehicle,
        "deadlines": deadlines,
        "notes": notes,
    }


def protest_window(liquidation_date, today=None):
    """Batch helper: (protest_by_iso, days_left, open) for one row, or
    (None, None, None) when the liquidation date is unknown."""
    today = today or date.today()
    l_date = parse_date(liquidation_date)
    if not l_date:
        return None, None, None
    protest_by = l_date + timedelta(days=PROTEST_WINDOW_DAYS)
    days_left = (protest_by - today).days
    return protest_by.isoformat(), days_left, days_left >= 0
