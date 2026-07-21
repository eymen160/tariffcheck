#!/usr/bin/env python3
"""Parse WCO Correlation Table II (HS2022 → HS2028) into a lookup DB.

Source: wcoomd.org "Tables II correlating the HS 2022 version to the HS 2028
version" PDF (published April 2026; 800KB, 27 pages). Line grammar observed:

  "0306.17 0310.62 ○ Argentine red shrimps..."   → new HS2022 entry + first target
  "0310.68 ○ Other shrimps and prawns"           → additional target (continuation)
  headers/footers                                 → skipped

A 2022 subheading ABSENT from the table is unchanged in HS 2028. One target →
renumbered; multiple targets → split (needs human review — the known failure
mode from HS 2022 migrations is blind crosswalk reliance on one-to-many).

Output: backend/data/hs2028_correlations.json.gz
  {"6digit_2022": {"targets": [{"code": "...", "note": "..."}]}}
"""
import gzip
import json
import re
from pathlib import Path

import pdfplumber

HERE = Path(__file__).parent
SRC = HERE / "hs2028_table2.pdf"
OUT = HERE.parent / "backend" / "data" / "hs2028_correlations.json.gz"

# Codes may carry the "ex" prefix: only PART of that subheading's goods
# transfer. Both source and target can be ex-coded.
CODE = r"(?:ex\s?)?\d{4}\.\d{2}"
TWO_CODES = re.compile(rf"^({CODE})\s+({CODE})\s*(.*)$")
ONE_CODE = re.compile(rf"^({CODE})\s*(.*)$")
SKIP = re.compile(
    r"^(Brief description|2022 Version|2028 Version|Table|Page|\d+\s*/\s*\d+|"
    r"CORRELATION|©|-\s*\d+\s*-)", re.IGNORECASE)


def split_code(token):
    """('0302.86', True) for 'ex0302.86'; ('0302.86', False) otherwise."""
    token = token.strip()
    if token.lower().startswith("ex"):
        return token[2:].strip(), True
    return token, False


def clean_note(text):
    text = text.strip().lstrip("○").strip()
    text = re.sub(r"\s+", " ", text)
    return text or None


def main():
    table = {}
    current = None
    with pdfplumber.open(SRC) as pdf:
        # Page 0 is the title page + explanatory notes with worked examples
        # that would otherwise pollute the table — the data starts on page 1.
        for page in pdf.pages[1:]:
            for raw in (page.extract_text() or "").splitlines():
                line = raw.strip()
                if not line or SKIP.match(line):
                    continue
                m = TWO_CODES.match(line)
                if m:
                    src_tok, dst_tok, note = m.groups()
                    src, src_partial = split_code(src_tok)
                    dst, dst_partial = split_code(dst_tok)
                    current = src
                    entry = table.setdefault(
                        src, {"partial": src_partial, "targets": []})
                    entry["partial"] = entry["partial"] or src_partial
                    entry["targets"].append(
                        {"code": dst, "partial": dst_partial,
                         "note": clean_note(note)})
                    continue
                m = ONE_CODE.match(line)
                if m and current:
                    dst_tok, note = m.groups()
                    dst, dst_partial = split_code(dst_tok)
                    table[current]["targets"].append(
                        {"code": dst, "partial": dst_partial,
                         "note": clean_note(note)})
                    continue
                # Wrapped remark text: append to the last target's note.
                if current and table[current]["targets"]:
                    last = table[current]["targets"][-1]
                    extra = clean_note(line)
                    if extra:
                        last["note"] = f"{last['note']} {extra}" if last["note"] else extra

    # Dedupe repeated (code, note) targets — explanatory blocks inside the
    # table can restate correlations already listed.
    for entry in table.values():
        seen, unique = set(), []
        for t in entry["targets"]:
            key = (t["code"], t["partial"], t["note"])
            if key not in seen:
                seen.add(key)
                unique.append(t)
        entry["targets"] = unique

    splits = sum(1 for v in table.values() if len(v["targets"]) > 1)
    print(f"2022 subheadings affected: {len(table)}  "
          f"(splits/one-to-many: {splits})")
    with gzip.open(OUT, "wt") as f:
        json.dump(table, f)
    print(f"wrote {OUT} ({OUT.stat().st_size/1024:.0f} KB)")


if __name__ == "__main__":
    main()
