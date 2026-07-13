#!/usr/bin/env python3
"""Test every generated data file against the live TariffCheck deployment.

Phase 1 — the 3 batch_rows_*.json bodies against /api/analyze-batch
          (deterministic, fast).
Phase 2 — all 57 PDF invoices, one by one, against /api/analyze
          (full Claude audit + USITC verification). Paced to respect the
          10-requests-per-5-minutes rate limit; 429s honor Retry-After.

Because every line's HTS code comes from a binding CBP ruling, a
"misclassification" finding against one of these lines is *presumed false
positive* — that comparison is the accuracy benchmark this run produces.

Results stream to live_test_results.jsonl; summary printed at the end.
"""
import json
import mimetypes
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

HERE = Path(__file__).parent
BASE = "https://tariffcheck-zeta.vercel.app"
OUT = HERE / "live_test_results.jsonl"
PACE_SECONDS = 32  # 10 req / 300 s → one every 30 s, plus margin


def post_json(path, body):
    req = urllib.request.Request(
        BASE + path, data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.status, json.load(r)


def post_pdf(path, pdf_path):
    boundary = uuid.uuid4().hex
    data = pdf_path.read_bytes()
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{pdf_path.name}"\r\n'
        f"Content-Type: application/pdf\r\n\r\n"
    ).encode() + data + f"\r\n--{boundary}--\r\n".encode()
    req = urllib.request.Request(
        BASE + path, data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST")
    with urllib.request.urlopen(req, timeout=180) as r:
        return r.status, json.load(r)


def record(rec):
    with OUT.open("a") as f:
        f.write(json.dumps(rec) + "\n")


def main():
    OUT.write_text("")
    dataset = json.loads((HERE / "cross_rulings_dataset.json").read_text())
    truth = {}  # normalized code -> set of ruling numbers (ground truth)
    for r in dataset:
        truth.setdefault(r["hts_code"].replace(".", ""), set()).add(r["ruling_number"])

    # ---------- Phase 1: deterministic batch ----------
    print("=== Phase 1: /api/analyze-batch ===")
    batch_files = sorted(HERE.glob("batch_rows_*.json"))
    for n, bf in enumerate(batch_files, 1):
        body = json.loads(bf.read_text())
        t0 = time.time()
        try:
            status, out = post_json("/api/analyze-batch", body)
        except urllib.error.HTTPError as e:
            print(f"batch {n}: HTTP {e.code} {e.read()[:200]}")
            record({"phase": "batch", "file": f"batch_rows_{n}.json", "http": e.code})
            continue
        s = out["summary"]
        nf = sum(1 for r in out["results"] if not r.get("current_code_found"))
        print(f"batch {n}: HTTP {status} rows={s['rows']} flagged={s['flagged']} "
              f"exposure=${s['total_estimated_exposure']:,.0f} "
              f"codes_not_found={nf} ({time.time()-t0:.1f}s)")
        record({"phase": "batch", "file": f"batch_rows_{n}.json", "http": status,
                "rows": s["rows"], "flagged": s["flagged"],
                "exposure": s["total_estimated_exposure"], "codes_not_found": nf,
                "flagged_rows": [r for r in out["results"] if r["status"] == "flagged"]})
        time.sleep(2)

    # ---------- Phase 2: PDFs through full AI audit ----------
    print("\n=== Phase 2: /api/analyze (PDF, one by one) ===")
    pdfs = sorted((HERE / "pdf_invoices").glob("*.pdf"))
    print(f"{len(pdfs)} PDFs, paced {PACE_SECONDS}s apart\n")

    for i, pdf in enumerate(pdfs, 1):
        t0 = time.time()
        attempt = 0
        while True:
            attempt += 1
            try:
                status, out = post_pdf("/api/analyze", pdf)
                break
            except urllib.error.HTTPError as e:
                if e.code == 429 and attempt <= 3:
                    wait = int(e.headers.get("Retry-After", "60"))
                    print(f"[{i}/{len(pdfs)}] {pdf.name}: 429, waiting {wait}s")
                    time.sleep(wait + 2)
                    continue
                body_txt = e.read().decode(errors="replace")[:300]
                print(f"[{i}/{len(pdfs)}] {pdf.name}: HTTP {e.code} {body_txt}")
                record({"phase": "pdf", "file": pdf.name, "http": e.code,
                        "error": body_txt})
                out = None
                break
            except Exception as e:
                if attempt <= 2:
                    time.sleep(20)
                    continue
                print(f"[{i}/{len(pdfs)}] {pdf.name}: {e}")
                record({"phase": "pdf", "file": pdf.name, "error": str(e)})
                out = None
                break

        if out is not None:
            findings = out.get("findings", [])
            ver = out.get("verification", {})
            # ground-truth check: misclassification claims against CBP-ruled codes
            fp_suspects = []
            for f in findings:
                cur = (f.get("hts_code") or "").replace(".", "")
                sug = (f.get("suggested_code") or "").replace(".", "")
                if cur in truth and sug and sug != cur:
                    fp_suspects.append({
                        "line_code": f.get("hts_code"),
                        "suggested": f.get("suggested_code"),
                        "confidence": f.get("confidence"),
                        "verified": f.get("verified"),
                        "savings": f.get("savings"),
                        "rulings": sorted(truth[cur]),
                        "explanation": (f.get("explanation") or "")[:200],
                    })
            rec = {
                "phase": "pdf", "file": pdf.name, "http": status,
                "findings": len(findings),
                "verified_count": ver.get("verified_count"),
                "total_count": ver.get("total_count"),
                "suppressed_count": ver.get("suppressed_count"),
                "total_savings": out.get("total_savings"),
                "fta_eligible": out.get("fta_eligible"),
                "section_301": out.get("section_301_applies"),
                "origin": out.get("country_of_origin"),
                "latency_ms": (out.get("meta") or {}).get("latency_ms"),
                "contradicts_cbp_ruling": fp_suspects,
                "elapsed_s": round(time.time() - t0, 1),
            }
            record(rec)
            flag = f" ⚠ {len(fp_suspects)} contradict CBP" if fp_suspects else ""
            print(f"[{i}/{len(pdfs)}] {pdf.name}: {len(findings)} findings, "
                  f"verified {ver.get('verified_count')}/{ver.get('total_count')}, "
                  f"savings ${out.get('total_savings') or 0:,.0f}, "
                  f"{rec['elapsed_s']}s{flag}")

        if i < len(pdfs):
            time.sleep(max(0, PACE_SECONDS - (time.time() - t0)))

    # ---------- Summary ----------
    print("\n=== SUMMARY ===")
    recs = [json.loads(l) for l in OUT.read_text().splitlines()]
    pdf_recs = [r for r in recs if r["phase"] == "pdf"]
    ok = [r for r in pdf_recs if r.get("http") == 200]
    print(f"PDFs: {len(ok)}/{len(pdf_recs)} analyzed successfully")
    if ok:
        tf = sum(r["findings"] for r in ok)
        tv = sum(r.get("verified_count") or 0 for r in ok)
        tt = sum(r.get("total_count") or 0 for r in ok)
        ts = sum(r.get("total_savings") or 0 for r in ok)
        fp = sum(len(r["contradicts_cbp_ruling"]) for r in ok)
        fp_hi = sum(1 for r in ok for s in r["contradicts_cbp_ruling"]
                    if s.get("confidence") == "high" and s.get("verified"))
        sup = sum(r.get("suppressed_count") or 0 for r in ok)
        print(f"suppressed (same-subheading, no rate delta): {sup}")
        lat = sorted(r["latency_ms"] or 0 for r in ok)
        print(f"findings: {tf} total, verification {tv}/{tt} verified")
        print(f"claimed savings across all invoices: ${ts:,.0f}")
        print(f"misclassification findings that contradict a binding CBP ruling "
              f"(presumed false positives): {fp} ({fp_hi} high-confidence+verified)")
        print(f"latency ms: median {lat[len(lat)//2]:,} max {lat[-1]:,}")


if __name__ == "__main__":
    main()
