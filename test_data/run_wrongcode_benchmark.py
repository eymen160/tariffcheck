#!/usr/bin/env python3
"""Wrong-code recovery benchmark — the published-accuracy protocol.

Protocol (documented for reproducibility):
- Sample N rulings (seeded, reproducible) from the public CROSS corpus
  (cross_rulings_dataset.json; every line's true code comes from a binding
  CBP ruling, in_2026_schedule only).
- Each ruling is presented to /api/analyze as an invoice line DECLARED under
  a deliberately wrong HTS code drawn from a *different chapter* of another
  sampled ruling (seeded rotation). A different-chapter decoy leaks nothing
  about the answer's neighborhood, so suggested-code accuracy measures real
  classification, not proximity guessing.
- Metrics:
    flag_rate        — % of runs where the audit raised a misclassification
                       finding against the declared line at all
    recovery@10/8/6/4 — % of runs where a suggested code matches the ruling's
                       code at that digit depth (best finding per run)
    verified_only    — all recovery numbers count only verified=true findings;
                       unverifiable suggestions score zero. The deterministic
                       verifier is part of the product being measured.
- Reference point: ATLAS (arXiv 2509.18400) reports 40% @10-digit / 57.5%
  @6-digit for its fine-tuned LLaMA-3.3-70B on full CROSS ruling texts. Our
  corpus descriptions are terser than full ruling texts (harder), and our
  task includes rejecting a decoy code (different). Numbers are comparable
  in spirit, not split-identical — say so wherever results are published.

Run: python3 run_wrongcode_benchmark.py [N] [--base URL]
Results stream to wrongcode_results.jsonl (resumable: already-done ruling
numbers are skipped on restart). Summary printed at the end and written to
wrongcode_summary.json.
"""
import json
import random
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).parent
BASE = "https://tariffcheck-zeta.vercel.app"
OUT = HERE / "wrongcode_results.jsonl"
SUMMARY = HERE / "wrongcode_summary.json"
SEED = 2026
PACE_SECONDS = 32  # 10 req / 300 s anonymous limit, with margin


def build_sample(n):
    rulings = json.loads((HERE / "cross_rulings_dataset.json").read_text())
    pool = [r for r in rulings if r.get("in_2026_schedule")]
    rng = random.Random(SEED)
    sample = rng.sample(pool, min(n, len(pool)))
    # Seeded decoy assignment: rotate until the decoy's chapter differs.
    codes = [r["hts_code"] for r in sample]
    for i, rec in enumerate(sample):
        chapter = rec["hts_code"][:2]
        offset = 1
        while codes[(i + offset) % len(codes)][:2] == chapter:
            offset += 1
        rec["decoy_code"] = codes[(i + offset) % len(codes)]
    return sample


def invoice_text(rec):
    return (
        "COMMERCIAL INVOICE\n"
        f"Item: {rec['description']}\n"
        f"HTS: {rec['decoy_code']}  "
        f"Value: ${rec['declared_value']:,.2f}  "
        f"Origin: {rec.get('origin') or 'Unknown'}\n"
        f"Quantity: {rec.get('qty', 1)} {rec.get('qty_unit', 'units')}\n"
    )


def post_analyze(base, text):
    req = urllib.request.Request(
        base + "/api/analyze", data=json.dumps({"text": text}).encode(),
        headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.status, json.load(r)


def digits(code):
    return "".join(c for c in str(code or "") if c.isdigit())


def match_depth(suggested, truth):
    s, t = digits(suggested), digits(truth)
    for depth in (10, 8, 6, 4):
        if len(s) >= depth and len(t) >= depth and s[:depth] == t[:depth]:
            return depth
    return 0


def score(analysis, rec):
    """Best verified misclassification finding vs the ruling's true code."""
    best = 0
    flagged = False
    best_code = None
    for f in analysis.get("findings", []):
        if digits(f.get("hts_code")) != digits(rec["decoy_code"]):
            continue
        flagged = True
        if not f.get("verified"):
            continue
        d = match_depth(f.get("suggested_code"), rec["hts_code"])
        if d > best:
            best, best_code = d, f.get("suggested_code")
    return {"flagged": flagged, "match_depth": best, "suggested": best_code}


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 200
    base = BASE
    if "--base" in sys.argv:
        base = sys.argv[sys.argv.index("--base") + 1]

    sample = build_sample(n)
    done = set()
    if OUT.exists():
        for line in OUT.read_text().splitlines():
            try:
                done.add(json.loads(line)["ruling_number"])
            except (ValueError, KeyError):
                pass

    todo = [r for r in sample if r["ruling_number"] not in done]
    print(f"sample={len(sample)} done={len(done)} todo={len(todo)} base={base}")

    with OUT.open("a") as out:
        for i, rec in enumerate(todo):
            started = time.time()
            row = {"ruling_number": rec["ruling_number"],
                   "true_code": rec["hts_code"],
                   "decoy_code": rec["decoy_code"],
                   "description": rec["description"]}
            try:
                status, analysis = post_analyze(base, invoice_text(rec))
                row.update(score(analysis, rec))
                row["http"] = status
            except urllib.error.HTTPError as e:
                if e.code == 429:
                    wait = int(e.headers.get("Retry-After", "60"))
                    print(f"  429 — sleeping {wait}s")
                    time.sleep(wait + 2)
                    continue  # retry this record on the next loop pass
                row.update({"http": e.code, "error": e.reason,
                            "flagged": None, "match_depth": None})
            except Exception as e:  # noqa: BLE001 — record and continue
                row.update({"http": None, "error": str(e)[:200],
                            "flagged": None, "match_depth": None})
            out.write(json.dumps(row) + "\n")
            out.flush()
            print(f"[{len(done) + i + 1}/{len(sample)}] {rec['ruling_number']} "
                  f"flagged={row.get('flagged')} depth={row.get('match_depth')}")
            elapsed = time.time() - started
            if elapsed < PACE_SECONDS:
                time.sleep(PACE_SECONDS - elapsed)

    rows = [json.loads(l) for l in OUT.read_text().splitlines()]
    ok = [r for r in rows if r.get("match_depth") is not None]
    if not ok:
        print("no scorable rows")
        return
    summary = {
        "protocol": "wrong-code recovery, different-chapter decoy, seed=2026",
        "n_scored": len(ok),
        "n_errors": len(rows) - len(ok),
        "flag_rate": round(sum(1 for r in ok if r["flagged"]) / len(ok), 4),
        **{f"recovery@{d}": round(
            sum(1 for r in ok if (r["match_depth"] or 0) >= d) / len(ok), 4)
           for d in (10, 8, 6, 4)},
        "reference": "ATLAS (arXiv 2509.18400): 40% @10, 57.5% @6 — "
                     "full ruling texts, no decoy; comparable in spirit only",
    }
    SUMMARY.write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
