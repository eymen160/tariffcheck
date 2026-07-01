#!/usr/bin/env python3
"""Build the TariffCheck HTS database from the official USITC HTS export.

Usage:
    python3 build_hts_db.py --download            # fetch from hts.usitc.gov, then build
    python3 build_hts_db.py --src /path/to/chunks # build from pre-downloaded JSON chunks

Reads the USITC "exportList" JSON (the same data behind hts.usitc.gov) and
emits hts_db.json.gz — one record per HTS line that carries a code, with the
full hierarchical description path and parsed duty rates. Statistical
(10-digit) lines inherit their duty rate from the nearest rate-bearing parent,
exactly as printed in the schedule.
"""
import argparse
import gzip
import json
import re
import sys
import urllib.request
from pathlib import Path

USITC_URL = "https://hts.usitc.gov/reststop/exportList?from={f}&to={t}&format=JSON&styles=false"
RANGES = [("0101", "2000"), ("2001", "4000"), ("4001", "6000"), ("6001", "8000"), ("8001", "9999")]

PCT_RE = re.compile(r"^(\d+(?:\.\d+)?)\s*%$")
SPECIAL_SEG_RE = re.compile(r"(Free|\d+(?:\.\d+)?%|[^()]+?)\s*\(([^)]+)\)")


def parse_general(raw):
    """'Free' -> 0.0, '2.5%' -> 2.5, specific/compound duties -> None (raw kept)."""
    raw = (raw or "").strip()
    if not raw:
        return None
    if raw.lower() == "free":
        return 0.0
    m = PCT_RE.match(raw)
    return float(m.group(1)) if m else None


def parse_special(raw):
    """'Free (A,AU,CA,MX,...) 3% (JO)' -> {'A': 0.0, 'AU': 0.0, ..., 'JO': 3.0}"""
    out = {}
    for rate_str, programs in SPECIAL_SEG_RE.findall(raw or ""):
        rate = parse_general(rate_str.strip())
        for prog in programs.split(","):
            prog = prog.strip()
            if prog:
                out[prog] = rate
    return out


def build(entries):
    records = {}
    # Stacks keyed by indent level
    desc_stack = []   # (indent, description)
    rate_stack = []   # (indent, general_raw, general_parsed, special_raw, units)

    for e in entries:
        indent = int(e.get("indent") or 0)
        desc = (e.get("description") or "").strip().rstrip(":")
        htsno = (e.get("htsno") or "").strip()
        general_raw = (e.get("general") or "").strip()
        special_raw = (e.get("special") or "").strip()
        units = e.get("units") or []

        while desc_stack and desc_stack[-1][0] >= indent:
            desc_stack.pop()
        while rate_stack and rate_stack[-1][0] >= indent:
            rate_stack.pop()

        desc_stack.append((indent, desc))
        if general_raw:
            rate_stack.append((indent, general_raw, parse_general(general_raw), special_raw, units))

        if not htsno:
            continue
        digits = re.sub(r"\D", "", htsno)
        if len(digits) not in (4, 6, 8, 10):
            continue

        # Rate: own if present, else inherit from nearest rate-bearing ancestor
        if general_raw:
            g_raw, g, s_raw, u = general_raw, parse_general(general_raw), special_raw, units
        elif rate_stack:
            _, g_raw, g, s_raw, u = rate_stack[-1]
        else:
            g_raw, g, s_raw, u = "", None, "", units

        full_desc = " — ".join(d for _, d in desc_stack if d)
        rec = {
            "code": htsno,
            "description": full_desc,
            "leaf": desc,
            "general_raw": g_raw,
            "level": len(digits),
            "chapter": digits[:2],
        }
        if g is not None:
            rec["general_rate"] = g
        special = parse_special(s_raw)
        if special:
            rec["special_rates"] = special
        if u:
            rec["units"] = u
        records[digits] = rec

    return records


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--download", action="store_true")
    ap.add_argument("--src", type=Path, help="dir with hts_<from>_<to>.json chunks")
    ap.add_argument("--out", type=Path, default=Path(__file__).parent / "hts_db.json.gz")
    args = ap.parse_args()

    entries = []
    for f, t in RANGES:
        if args.download:
            print(f"downloading {f}-{t}...", file=sys.stderr)
            with urllib.request.urlopen(USITC_URL.format(f=f, t=t), timeout=120) as r:
                entries.extend(json.load(r))
        else:
            src = (args.src or Path(".")) / f"hts_{f}_{t}.json"
            entries.extend(json.loads(src.read_text()))

    records = build(entries)
    by_level = {}
    rated = sum(1 for r in records.values() if "general_rate" in r)
    for r in records.values():
        by_level[r["level"]] = by_level.get(r["level"], 0) + 1

    with gzip.open(args.out, "wt", encoding="utf-8") as fh:
        json.dump(records, fh, separators=(",", ":"), ensure_ascii=False)

    print(f"wrote {args.out}: {len(records)} codes "
          f"(levels: {sorted(by_level.items())}), {rated} with parsed ad-valorem rate, "
          f"{args.out.stat().st_size / 1e6:.1f} MB gzipped")


if __name__ == "__main__":
    main()
